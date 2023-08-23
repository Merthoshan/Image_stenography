import streamlit as st
from PIL import Image
import numpy as np
import os

def charToBin(text):
    # ascii 32 represents space so we replace space with 00100000 to avoid the error
    binText = ''.join(format(ord(char), '08b') if char != ' ' else '00100000' for char in text)
    return binText

def giveEncryptionString(message, password):
    bit_message = charToBin(message)
    bit_password = charToBin(password)
    
    password_length = len(password)
    password_length_bit = format(password_length, '08b')
    
    delimiter = '00111100'  # New delimiter, can be any binary sequence that's less likely to appear
    
    # Embedding the message, delimiter, password length, and password
    binary_msg = bit_message + delimiter + password_length_bit + bit_password
    return binary_msg


def encrypt_message(image_path, message, password):
    # Open the image file
    img = Image.open(image_path)

    # Convert the image to RGBA mode
    img = img.convert("RGBA")

    # Getting the dimensions of the image
    width, height = img.size

    # Getting a 2D array of the shape (height * width, 4)
    # Each row represents a pixel, and each column represents a color channel (RGBA)
    array = np.array(list(img.getdata()))
    
    array = array.astype(np.uint8)

    color_channels = 3

    total_pixels = array.shape[0] 
        
    binary_message = giveEncryptionString(message, password)
    print(binary_message)
    print("before mnauplation")
    # print(array)
  
    # Each pixel has 4 color channels (RGBA), and we can modify the last 2 bits of each RGB channel,
    total_bits = len(binary_message)
    req_channels =  total_bits // 2

    if len(binary_message) % 2 != 0:
        req_channels += 1

    if req_channels > total_pixels * color_channels:
        print("ERROR: Need a larger file size")
        return
    else:
        index = 0
        for p in range(total_pixels):
            if index >= len(binary_message):
              break
            # Get the current pixel value
            pixel = array[p]

            # Modify the last 2 bits of each RGB channel using the message
            for c in range(color_channels):
                # 0b11111100 is a bit mask that when '&' is performed clears the last 2 bits of the pixel
                pixel[c] = (pixel[c] & 0b11111100) | int(binary_message[index:index+2], 2)

                # Increment the index pointer to track the next 2 bits of the message
                index = (index + 2) 

                # Update the pixel value in the image array
                array[p] = pixel
        
    # Convert the pixel values to the appropriate data type
    array = array.astype(np.uint8)

    # Reshape the 2D array back to the original image dimensions
    array = array.reshape(height, width, 4)  # 4 channels (RGBA)
    print("after manuplation")
    print(array)

    # Convert the modified array back into an image
    modified_img = Image.fromarray(array, "RGBA")

    # Get the original image's name without the extension
    modified_image_name = os.path.splitext(os.path.basename(image_path))[0]

    # Append "_enc" to the image name
    new_image_name = modified_image_name + "_enc"

    # Save the image as PNG with the modified name
    new_image_path = new_image_name + ".png"
    modified_img.save(new_image_path, "PNG")
    print("Image is encoded and saved successfully")
    
    return new_image_path

def encrypt_page():
    st.title("Image Encryption")
    
    # Placeholder image path for when no image is uploaded
    default_image_path = "path_to_default_image.png"
    
    image_path = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
    
    # Use the uploaded image or the default image
    if image_path is None:
        st.image(default_image_path, caption="Default Image", use_column_width=True)
    else:
        st.image(image_path, caption="Uploaded Image", use_column_width=True)
        
        message = st.text_area("Enter Message:")
        password = st.text_input("Enter Password:")

        if st.button("Encrypt"):
            # Perform encryption and get the new image path
            new_image_path = encrypt_message(image_path, message, password)
            st.success(f"Image is encoded and saved successfully as '{new_image_path}'")

            # Provide a download link for the encrypted image
            st.markdown(f"**[Download Encrypted Image]({new_image_path})**")


# Page to drag and drop an image path for decryption
def decrypt_page():
    st.title("Image Decryption")
    st.write("Drag and drop an encrypted image file for decryption.")
    image_path = st.file_uploader("Upload Encrypted Image", type=["jpg", "jpeg", "png"])
    if image_path:
        st.image(image_path, caption="Uploaded Encrypted Image", use_column_width=True)
        # Add decryption logic here

def main():
    st.title("Image Encryption and Decryption App")

    # Sidebar with buttons for navigation
    selection = st.sidebar.radio("Select an action:", ["Encrypt", "Decrypt"])

    # Page navigation based on button selection
    if selection == "Encrypt":
        encrypt_page()
    elif selection == "Decrypt":
        decrypt_page()

if __name__ == "__main__":
    main()
