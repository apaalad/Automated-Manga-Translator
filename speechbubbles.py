#!/usr/bin/env python
# coding: utf-8

# In[1]:


import cv2
import numpy as np


# In[1]:


def find_bubbles(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    new_image = cv2.convertScaleAbs(gray, alpha=0.15, beta=0)
    thresh = cv2.adaptiveThreshold(new_image, 255, 1, 1, 11, 2)

    h, w = gray.shape[:2]
    mask = np.zeros((h+2, w+2), np.uint8)
    cv2.floodFill(thresh, mask, (0,0), 255);
    # Invert floodfilled image
    filled = cv2.bitwise_not(thresh)

    blur = cv2.GaussianBlur(filled,(101,101),0)
    filled = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)[1]

    kernel1 = np.ones((3,3),np.uint8)
    kernel2 = np.ones((5,1),np.uint8)
    filled = cv2.erode(filled,kernel1,iterations =4) 
    filled = cv2.dilate(filled,kernel2,iterations =1)

    ret3,th3 = cv2.threshold(filled,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    
    contours, hierarchy= cv2.findContours(th3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bubbles=[]
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        bubbles.append(image[y:y+h, x:x+w])
        
    return bubbles


# In[2]:


def to_rect(img):##
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width=gray.shape
    (t,thresh) = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    kernel = np.ones((2,2),np.uint8)
    thresh = cv2.erode(thresh,kernel,iterations =1) 
    thresh = cv2.dilate(thresh,kernel,iterations =1)
    for i in range(height):
        for j in range(width):
            if thresh[i][j]==255:
                break 
            thresh[i][j]=255
        for j in range(width-1,-1,-1):
            if thresh[i][j]==255:
                break 
            thresh[i][j]=255  
    return thresh


# In[ ]:




