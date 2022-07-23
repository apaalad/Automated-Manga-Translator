#!/usr/bin/env python
# coding: utf-8

# In[4]:


import numpy as np
import cv2
import matplotlib.pyplot as plt


# In[1]:


def pre_process(img):
    gray = img#cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    gray = cv2.medianBlur(gray,5)
    thresh=gray
# Apply adaptive threshold
    #thresh = cv2.adaptiveThreshold(gray, 255, 1, 1, 11, 2)
    kernel = np.ones((2,2),np.uint8)
    thresh = cv2.erode(thresh,kernel,iterations = 1) 
    thresh = cv2.dilate(thresh,kernel,iterations = 1)
    
    return thresh


# In[1]:


def segment_rows(image, og_image):
    # Width and heigth the image
    height, width = image.shape
    # Sum the value lines 
    vertical_px = np.sum(image, axis=0)
    # Normalize
    normalize = vertical_px/255
    avg=np.quantile(normalize,0.75)


    pts=[]
    m=normalize.min()+1
    #m=np.quantile(normalize,0.25)
    idx=0
    while(idx<width-1):
        if ((normalize[idx]<m) and (normalize[idx+1]>m)):
            a=idx
            j=idx+1
            while(normalize[j]>m):
                j+=1
                if j==width:
                    j=j-1
                    break
            b=j
            idx=j
            if normalize[a:b].max()>avg:
                pts.append((a,b))
        else:
            idx+=1

    img=[]
    og_img=[]
    for i in range(len(pts)-1,-1,-1):# reading right to left
        img.append(image[:,pts[i][0]-5:pts[i][1]+5])
        og_img.append(og_image[:,pts[i][0]-5:pts[i][1]])
    
    return img,og_img


# In[2]:


def segment_char(image,og_image):
    kernel = np.ones((4,1),np.uint8)
    image1= cv2.dilate(image,kernel,iterations = 1)
    height, width = image.shape
    horizontal_px = np.sum(image1, axis=1)
# Normalize
    normalize = horizontal_px/255
    pts=[]
    level=[]
    m=normalize.min()+1 ##+1 for rounding errors
    idx=0
    while(idx<height-1):
        if ((normalize[idx]<m) and (normalize[idx+1]>m)):
            a=idx
            j=idx+1
            s=normalize[a]
            while(normalize[j]>m):
                s+=normalize[j]
                j+=1
                if j==height:
                    break
            b=j
            idx=j
            pts.append((a,b))
            level.append(s/(b-a))
        else:
            idx+=1
        char=[]    
        for i in range(len(pts)):
            if pts[i][1]-pts[i][0]>12:##only taller than a level removing '...'
                char.append(og_image[pts[i][0]-3:pts[i][1]+3,:])

    return char


# In[3]:


def segmented_sentence(img):
    img1=pre_process(img)
    rows1,rows=segment_rows(img1,img)
    chars=[]
    for i in range(len(rows)):
        chars.append(segment_char(rows1[i],rows[i]))
    return chars


# In[ ]:





# In[ ]:




