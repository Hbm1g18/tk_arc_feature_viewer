import os
import pandas as pd
from arcgis.gis import GIS
from tqdm import tqdm
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog

username = ""
password = ""

gis = GIS(username=username, password=password)

FeatureLayerID = "14718ae8c8d846bcb857bad1b8570352"

print(f"Connected as {username}")

FeatureLayer = gis.content.get(FeatureLayerID)
layer = FeatureLayer.layers[0]

features = layer.query(where='1=1', return_geometry=False).features

# Create a list to store OID and Attachment ID information
attachment_list = []

# Use tqdm to create a progress bar
for feature in tqdm(features, desc="Processing Features", unit=" feature"):
    oid = feature.attributes['OBJECTID']
    
    # Get attachment information for the OID
    attachments_info = layer.attachments.get_list(oid=oid)
    
    # Check if there are attachments for the OID
    if attachments_info:
        # Add OID, Attachment ID, and Filename to the list
        for attachment_info in attachments_info:
            att_id = attachment_info['id']
            filename = attachment_info['name']
            attachment_list.append({'OID': oid, 'AttachmentID': att_id, 'Filename': filename})

# Create a DataFrame for the attachment list
attachment_df = pd.DataFrame(attachment_list)

# Create an empty DataFrame for attributes
attributes_df = pd.DataFrame()


for index, row in tqdm(attachment_df.iterrows(), desc="Fetching Attributes", unit=" row"):
    oid = row['OID']
    att_id = row['AttachmentID']
    
    # Get attributes for the OID
    attributes = layer.query(where=f'OBJECTID={oid}', return_geometry=False).sdf
    
    # Add a column for Attachment ID and Filename
    attributes['AttachmentID'] = att_id
    attributes['Filename'] = row['Filename']
    

    attributes_df = pd.concat([attributes_df, attributes])

print(attributes_df)


class ImageDisplayGUI:
    def __init__(self, root, df):
        self.root = root
        self.df = df
        self.current_index = 0

        # Set the initial size of the GUI
        root.geometry("800x500")

        # Create a frame to hold the image label, comments text box, and buttons
        frame = tk.Frame(root)
        frame.pack()

        # Set the initial size of the image label
        self.image_label = tk.Label(frame, width=300, height=200)
        self.image_label.grid(row=0, column=0, padx=10)

        # Add a text box for comments
        self.comments_textbox = tk.Text(frame, height=5, width=40)
        self.comments_textbox.grid(row=0, column=1, padx=10)

        # Create buttons for navigation and saving
        self.previous_button = tk.Button(frame, text="Previous", command=self.previous_row)
        self.previous_button.grid(row=1, column=0, pady=10)

        self.save_button = tk.Button(frame, text="Save", command=self.save_comments)
        self.save_button.grid(row=1, column=1, pady=10)

        self.next_button = tk.Button(frame, text="Next", command=self.next_row)
        self.next_button.grid(row=1, column=2, pady=10)

        self.update_image()

    def update_image(self):
        if 0 <= self.current_index < len(self.df):
            oid = self.df.iloc[self.current_index]['OBJECTID']
            filename = self.df.iloc[self.current_index]['Filename']
            comments = self.df.iloc[self.current_index]['Comments']

            image_path = f"C:/Users/HarryBM/Desktop/Tex/outfolder/{oid}/{filename}"

            if os.path.exists(image_path):
                # Open the image and resize while maintaining aspect ratio
                image = Image.open(image_path)
                image = image.resize((300, 200), Image.ANTIALIAS)

                # Create a PhotoImage object
                image = ImageTk.PhotoImage(image)

                # Configure the image label with the new image
                self.image_label.config(image=image)
                self.image_label.image = image

                # Set the comments text box with the 'Comments' column value
                self.comments_textbox.delete(1.0, tk.END)  # Clear previous text
                self.comments_textbox.insert(tk.END, comments)
            else:
                print(f"Image not found: {image_path}")

    def save_comments(self):
        if 0 <= self.current_index < len(self.df):
            # Update the 'Comments' column in the dataframe with the text box content
            new_comments = self.comments_textbox.get("1.0", tk.END).strip()
            self.df.at[self.current_index, 'Comments'] = new_comments
            print(f"Comments for row {self.current_index} saved: {new_comments}")

    def next_row(self):
        self.current_index += 1
        if self.current_index >= len(self.df):
            self.current_index = 0
        self.update_image()

    def previous_row(self):
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.df) - 1
        self.update_image()
        # After updating the image, update the text box with the new 'Comments' value
        comments = self.df.iloc[self.current_index]['Comments']
        self.comments_textbox.delete(1.0, tk.END)
        self.comments_textbox.insert(tk.END, comments)

# Create Tkinter root window
root = tk.Tk()
root.title("Image Viewer")

gui = ImageDisplayGUI(root, attributes_df)

root.mainloop()