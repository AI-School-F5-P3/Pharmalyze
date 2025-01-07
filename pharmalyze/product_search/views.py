# product_search/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
from .vector_store import VectorStore
from .utils import process_query, analyze_image
from .models import Product, KnowledgeBase
from openai import OpenAI
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
vector_store = VectorStore()

@csrf_exempt
@require_http_methods(["GET", "POST"])
def search_view(request):
    """Handle search requests"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            
            if not query:
                return JsonResponse({'error': 'Query is required'}, status=400)
            
            # Determine query type
            query_type, confidence = process_query(query)
            
            if query_type == 'product':
                results = handle_product_search(query)
            else:
                results = handle_knowledge_search(query)
            
            return JsonResponse({
                'query_type': query_type,
                'confidence': confidence,
                'results': results
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Search error: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    return render(request, 'product_search/search.html')

def handle_product_search(query: str) -> Dict[str, Any]:
    """Handle product-related searches"""
    results = vector_store.semantic_search(
        query=query,
        collection_name='products',
        n_results=5,
        threshold=0.7
    )
    
    # Enhance results with additional product information
    enhanced_results = []
    for metadata in results['metadatas']:
        product = Product.objects.get(id=metadata['id'])
        enhanced_results.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'category': product.category,
            'image_url': product.get_image_url(),
            'metadata': product.metadata
        })
    
    return {'products': enhanced_results}

def handle_knowledge_search(query: str) -> Dict[str, Any]:
    """Handle knowledge-related searches"""
    # Get relevant knowledge base entries
    knowledge_results = vector_store.semantic_search(
        query=query,
        collection_name='knowledge',
        n_results=3,
        threshold=0.6
    )
    
    # Use GPT-4 to generate response
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    context = "\n".join([doc for doc in knowledge_results['documents']])
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": """You are a knowledgeable pharmacy assistant. 
                Use the provided context to answer questions accurately.
                If the information isn't in the context, say so clearly."""
            },
            {
                "role": "user",
                "content": f"Context: {context}\n\nQuestion: {query}"
            }
        ]
    )
    
    # Prepare sources information
    sources = [
        {
            'title': meta['title'],
            'category': meta['category'],
            'source_type': meta['source_type']
        }
        for meta in knowledge_results['metadatas']
    ]
    
    return {
        'answer': response.choices[0].message.content,
        'sources': sources
    }

@csrf_exempt
@require_http_methods(["POST"])
def analyze_product_image(request):
    """Analyze product image using GPT-4 Vision"""
    try:
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image provided'}, status=400)
        
        image = request.FILES['image']
        image_path = default_storage.save(
            f'temp/product_analysis/{image.name}',
            image
        )
        
        try:
            analysis_result = analyze_image(image_path)
            return JsonResponse({'analysis': analysis_result})
        finally:
            # Clean up temporary file
            default_storage.delete(image_path)
            
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Image analysis failed'}, status=500)