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

def decrypt_image(image_path, password):
    img = Image.open(image_path)

    # Convert the image to RGBA mode
    img = img.convert("RGBA")

    array = np.array(img)
    
    array = array.astype(np.uint8) 
     
    last_two_bits = np.bitwise_and(array[..., :3], 0b00000011)  # Extract last two bits of RGB channels

    image_binary = last_two_bits.reshape(-1, 3)  # Reshape to (total_pixels, color_channels)
    image_binary = ''.join(format(pixel, '02b') for pixel in image_binary.flatten())  # Convert to string

    delimiter = '00111100'  # Delimiter bit pattern

    delimiter_start_index = image_binary.find(delimiter)

    if delimiter_start_index != -1:
        remainder = 8 - (delimiter_start_index % 8)

        if delimiter_start_index % 8 != 0:
            delimiter_start_index += remainder

        delimiter_end_index = delimiter_start_index + len(delimiter)

        password_length_start = delimiter_end_index
        password_length_end = password_length_start + 8
        password_length_bin = image_binary[password_length_start:password_length_end]

        password_length = int(password_length_bin, 2)

        password_start = password_length_end
        password_end = password_start + (password_length * 8)
        extractedBin_password = image_binary[password_start:password_end]

        extracted_password = ''.join(chr(int(extractedBin_password[i:i+8], 2)) for i in range(0, len(extractedBin_password), 8))

        if extracted_password == password:
            extracted_message = ''.join(chr(int(image_binary[i:i+8], 2)) for i in range(0, delimiter_start_index, 8))
            return extracted_message
        else:
            raise Exception("Incorrect password")
    else:
        raise Exception("Password not found! Make sure you have uploaded the correct image")

import base64

def get_image_download_link(img_path, filename):
    with open(img_path, "rb") as img_file:
        encoded_img = base64.b64encode(img_file.read()).decode()
    href = f'<a href="data:image/png;base64,{encoded_img}" download="{filename}">Click here to download</a>'
    return href

def encrypt_page():
    st.title("Image Encryption")
    
    default_image_path = "path_to_default_image.png"
    uploaded_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
    
    if uploaded_image is None:
        st.image(default_image_path, caption="Default Image", use_column_width=True)
        image_path = default_image_path
    else:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        image_path = "uploaded_image.png"
        image.save(image_path, format="PNG")
        
        message = st.text_area("Enter Message:")
        password = st.text_input("Enter Password:")
        
        if message and password:
            if st.button("Encrypt"):
                new_image_path = encrypt_message(image_path, message, password)
                st.success(f"Image is encoded and saved successfully as '{new_image_path}'")

                # Provide a download link for the encrypted image
                st.markdown(get_image_download_link(new_image_path, "encrypted_image.png"), unsafe_allow_html=True)


# Page to drag and drop an image path for decryption
def decrypt_page():
    st.title("Image Decryption")
    st.write("Drag and drop an encrypted image file for decryption.")
    image_path = st.file_uploader("Upload Encrypted Image", type=["jpg", "jpeg", "png"])
    
    if image_path:
        st.image(image_path, caption="Uploaded Encrypted Image", use_column_width=True)
        
        password = st.text_input("Enter Password:")
        
        if password:
            if st.button("Decrypt"):
                try:
                    decrypted_message = decrypt_image(image_path, password)
                    st.success("Decryption Successful")
                    st.text_area("Decrypted Message:", decrypted_message)
                except Exception as e:
                        st.error(str(e))
        else:
            st.warning("Please provide the password.")
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
