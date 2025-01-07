# prescription/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Prescription
import pytesseract
from PIL import Image
import cv2
import numpy as np

@login_required
def prescription_upload(request):
    if request.method == 'POST' and request.FILES.get('prescription_image'):
        try:
            prescription = Prescription(image=request.FILES['prescription_image'])
            prescription.save()
            return redirect('prescription:analyze', prescription_id=prescription.id)
        except Exception as e:
            messages.error(request, f'Error uploading prescription: {str(e)}')
    return render(request, 'prescription/upload.html')

@login_required
def analyze_prescription(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    try:
        # Read the image using OpenCV
        image_path = prescription.image.path
        img = cv2.imread(image_path)
        
        # Preprocess the image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply thresholding
        thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Convert the image for Tesseract
        pil_img = Image.fromarray(thresh)
        
        # Perform OCR
        prescription.processed_text = pytesseract.image_to_string(pil_img)
        prescription.status = 'completed'
        prescription.save()
        
        return redirect('prescription:results', prescription_id=prescription.id)
        
    except Exception as e:
        prescription.status = 'failed'
        prescription.save()
        messages.error(request, f'Error analyzing prescription: {str(e)}')
        return redirect('prescription:upload')

@login_required
def prescription_results(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id)
    return render(request, 'prescription/results.html', {'prescription': prescription})

@login_required
def prescription_history(request):
    prescriptions = Prescription.objects.all().order_by('-uploaded_at')
    return render(request, 'prescription/history.html', {'prescriptions': prescriptions})