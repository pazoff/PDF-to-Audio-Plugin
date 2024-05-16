import os
import shutil
import time
from datetime import datetime
import subprocess
import PyPDF2
from pydub import AudioSegment
from typing import Dict
from cat.mad_hatter.decorators import tool, hook, plugin
from cat.log import log
import threading
from langchain.document_loaders.base import BaseBlobParser
from langchain.docstore.document import Document
from langchain.document_loaders.blob_loaders.schema import Blob
from typing import Iterator
from abc import ABC
from enum import Enum
from pydantic import BaseModel


# Settings

# Select box
# Add more readers from: https://rhasspy.github.io/piper-samples/
class ReaderSelect(Enum):
    Alice: str = 'Alice'
    Dave: str = 'Dave'
    Ruslan: str = 'Ruslan'


class PDFToAudioCatSettings(BaseModel):
    # Select
    Reader: ReaderSelect = ReaderSelect.Alice


# Give your settings schema to the Cat.
@plugin
def settings_schema():
    return PDFToAudioCatSettings.schema()

pdf_data_dir = "/admin/assets/pdftoaudio/"


def check_ffmpeg_installation():
    try:
        # Check if ffmpeg is installed
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("ffmpeg is already installed.")
    except:
        # If ffmpeg is not installed, attempt to install it
        install_ffmpeg()

def install_ffmpeg():
    try:
        # Install ffmpeg using a package manager (adjust the command based on your system's package manager)
        process = subprocess.Popen(['apt', 'update'])
        # Wait for the process to finish
        process.wait()

        subprocess.run(['apt', '-y', 'install', 'ffmpeg'], check=True)
        print("ffmpeg has been successfully installed.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing ffmpeg: {e}")


def get_pdf_page_count(pdf_path):
    """
    Get the number of pages in a PDF file.

    Parameters:
    - pdf_path (str): The path to the PDF file.

    Returns:
    - int: The number of pages in the PDF.
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)
            return page_count
    except FileNotFoundError:
        print(f"Error: File not found - {pdf_path}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def convert_pdf_to_audio(pdf_input_filename: str, output_wav_filename: str, output_mp3_filename: str,
                         output_text_filename: str, selected_voice: str,
                         first_pdf_page: int, last_pdf_page: int, cat):
    
    try:
        # Record the start time
        start_time = time.time()

        


        # Read the contents of each page
        pdf_file = open(pdf_input_filename, 'rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        pdf_pages = len(pdf_reader.pages)
        if (int(last_pdf_page) == -1) or (last_pdf_page > pdf_pages):
            last_pdf_page = pdf_pages
        if first_pdf_page > last_pdf_page:
            first_pdf_page = 1
        print("Processing the PDF(pages from " + str(first_pdf_page) + " to " + str(
            last_pdf_page) + "), extracting and formatting the text ...")
        cat.send_ws_message(content="Processing the PDF pages from " + str(first_pdf_page) + " to " + str(
            last_pdf_page) + " ...", msg_type='chat')

        # Extract all the text
        text = ""
        # len(pdf_reader.pages)
        for page in range(first_pdf_page - 1, last_pdf_page):
            text += pdf_reader.pages[page].extract_text()

        # Prepare the text. Remove some special chars
        text = text.replace('\n', ' ').replace('\r', ' ').replace('•', ' ').replace('~', ' ').replace('#',
                                                                                                      ' ').replace(
            '*', ' ').replace('■', ' ').replace('®', ' ').replace('©', ' ')

        text = " ".join(text.split())
        text = text.replace('. ', '.\n')
        while ".\n.\n" in text:
            text = text.replace('.\n.\n', '.\n')
        text = text.replace(' .', '.')
        print("Done.")

        # Do we have text?
        if len(text) > 0:
            
            # Save the text to a text file
            with open(output_text_filename, "w") as f:
                f.write(text)

            # Generated text file info
            print("* The text file is " + str(
                int((os.path.getsize(output_text_filename) / 1024) * 100) / 100) + " kB (" + str(
                int((os.path.getsize(output_text_filename) / 1024 / 1024) * 100) / 100) + " MB)")

            # 0.003594915 seconds per bite
            # 0.018959232 is calculated on 195 min base(3h15min)
            
            esti_coef = 0.005103186
            
            # how to calculate esti_coef(=X_your_coef) for your system
            # Estimated completion time --> esti_coef
            # execution_time_seconds --> X_your_coef
            # (execution_time_seconds * esti_coef) / Estimated completion time = X_your_coef
            # set esti_coef = X_your_coef

            estimated_message = "Estimated completion time: " + str(
                int((os.path.getsize(output_text_filename) * esti_coef) * 100) / 100) + " seconds = " + str(
                int((os.path.getsize(output_text_filename) * esti_coef / 60) * 100) / 100) + " minutes = " + str(
                int((os.path.getsize(output_text_filename) * esti_coef / 3600) * 100) / 100) + " hours."
            print(estimated_message)
            cat.send_ws_message(content=estimated_message, msg_type='chat')

            # Generate the speech audio
            # Open the text file
            read_text_file = open(output_text_filename, "r")
            # Open the wav file
            #save_wav_file = open(output_wav_filename, "wb")

            # Text to speech command
            piper_cmd = ["piper", "--cuda"]

            # Selected voice
            if selected_voice not in ["Alice", "Dave", "Ruslan"]:
                selected_voice = "Dave"
            if selected_voice == "Alice":
                piper_cmd.append("--model")
                piper_cmd.append("en_US-lessac-high")
            if selected_voice == "Dave":
                piper_cmd.append("--model")
                piper_cmd.append("en_US-ryan-high")
            if selected_voice == "Ruslan":
                piper_cmd.append("--model")
                piper_cmd.append("ru_RU-ruslan-medium")

            piper_cmd.append(f"--output_file {output_wav_filename}")

            # Print piper commands
            m_cmd = ""
            for cmd in piper_cmd:
                m_cmd += (cmd + " ")
            print("\n* Executing: " + m_cmd + " < " + output_text_filename + " > " + output_wav_filename + "\n")

            # Execute piper conversion

            command_string = " ".join(piper_cmd)

            subprocess.run(command_string, stdin=read_text_file, shell=True, check=True)

            # Close the wav and txt files
            #save_wav_file.close()
            read_text_file.close()

        # Convert the wav file to mp3 and ogg
        if os.path.exists(output_wav_filename):
            if os.path.getsize(output_wav_filename) > 0:
                # Convert to mp3
                print("\n* Converting " + output_wav_filename + " file to " + output_mp3_filename + " ...")
                AudioSegment.from_wav(output_wav_filename).export(output_mp3_filename, format="mp3",
                                                                  bitrate="320")
                
                # Record the end time
                end_time = time.time()

                # Calculate the execution time in seconds
                execution_time_seconds = end_time - start_time

                # Convert the execution time to minutes
                execution_time_minutes = execution_time_seconds / 60

                print(f"Done in {execution_time_minutes:.2f} minutes")
                
                # Convert to ogg
                output_ogg_filename = output_mp3_filename[:(len(output_mp3_filename) - 4)] + ".ogg"
                print("\n* Converting " + output_wav_filename + " file to " + output_ogg_filename)
                AudioSegment.from_wav(output_wav_filename).export(output_ogg_filename, format="ogg")
                print("Done.")

                # Generate the audio player HTML and send it as a chat message
                audio_player = "<audio controls><source src='" + output_mp3_filename + "' type='audio/wav'>Your browser does not support the audio tag.</audio>"
                cat.send_ws_message(content=audio_player, msg_type='chat')
                cat.send_ws_message(content=f'The <a href="{output_mp3_filename}" target="_blank">MP3</a> (<a href="{output_wav_filename}" target="_blank">WAV</a>,<a href="{output_ogg_filename}" target="_blank">OGG</a>) was ready in {execution_time_minutes:.2f} minutes = {execution_time_seconds:.2f} seconds.', msg_type='chat')

        # Close the PDF file
        pdf_file.close()
    except Exception as e:
        log.error(f"Error converting {pdf_input_filename} to audio: {e}")
        cat.send_ws_message(content=f"Error converting <b>{pdf_input_filename}</b> to audio: {e}", msg_type='chat')


# End of convert_pdf_to_audio()

def do_convert_pdf_to_audio(pdf_file_name, cat, start_page=None, end_page=None):
    
    filepath = pdf_data_dir + pdf_file_name
    

    if not os.path.exists(filepath):
        print(f"The file {pdf_file_name} does not exist! Please, upload {pdf_file_name}.bin")
        pdf_files_available = str(find_pdf_files(pdf_data_dir, only_not_converted = True))
        if len(pdf_files_available) >= 2:
            pdf_files_available = pdf_files_available[1:-1]
        return f"The file {pdf_file_name} does not exist! Please, upload {pdf_file_name}.<b>bin</b><br>{pdf_files_available}"

    # Specify the folder path
    folder_path = filepath + "-audio"

    # Check if the folder exists, create it if not
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    wav_file_name = folder_path+"/"+pdf_file_name+".wav"
    mp3_file_name = folder_path+"/"+pdf_file_name+".mp3"
    txt_file_name = folder_path+"/"+pdf_file_name+".txt"

    # Load the settings
    settings = cat.mad_hatter.get_plugin().load_settings()
    selected_reader = settings.get("Reader")
    
    if start_page and end_page:
        if (start_page < 1) or (start_page > end_page):
            start_page = 1
        if end_page < start_page:
            end_page = -1
    else:
        start_page = 1
        end_page = -1
    
    tr = threading.Thread(target=convert_pdf_to_audio, args=(filepath, wav_file_name, mp3_file_name, txt_file_name, selected_reader, start_page, end_page, cat))
    tr.start()
    return f"Converting <b>{pdf_file_name}</b> to audio in the background. You can continue using the Cat ..."


def find_pdf_files(folder_path, only_not_converted=None):
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Folder '{folder_path}' didn't exist and has been created.")

        pdf_files = [file for file in os.listdir(folder_path) if file.endswith('.pdf')]

        if only_not_converted:
            pdf_files = [pdf for pdf in pdf_files if not os.path.exists(os.path.join(folder_path, f"{pdf}-audio"))]
        
        return pdf_files

    except PermissionError:
        print(f"Error: Permission denied for folder '{folder_path}'.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

def find_audio_files(folder_path, pdf_files):
    audio_files = []

    try:
        for pdf_name in pdf_files:

            audio_folder = os.path.join(folder_path, f"{pdf_name}-audio")

            if os.path.exists(audio_folder) and os.path.isdir(audio_folder):
                # Check for audio files in the "-audio" folder
                audio_files.extend([
                    os.path.join(audio_folder, f"{pdf_name}.mp3"),
                    os.path.join(audio_folder, f"{pdf_name}.wav"),
                    os.path.join(audio_folder, f"{pdf_name}.ogg")
                ])

    except Exception as e:
        print(f"An unexpected error occurred while searching for audio files: {e}")
        audio_files = []

    return audio_files

def list_audio_files(folder_path):
    try:
        pdf_files = find_pdf_files(folder_path)
        audio_files = find_audio_files(folder_path, pdf_files)

        result = []

        for pdf_file in pdf_files:
            #pdf_base, _ = os.path.splitext(pdf_file)
            pdf_base = pdf_file
            audio_folder = os.path.join(folder_path, f"{pdf_base}-audio")

            pdf_file_num_pages = get_pdf_page_count(folder_path + "/" + pdf_file)

            if os.path.exists(audio_folder) and os.path.isdir(audio_folder):
                result.append(f"<b>{pdf_base}</b> - <i>{pdf_file_num_pages}</i> pages: <a href='{audio_folder}/{pdf_base}.mp3' target='_blank'>MP3</a> <a href='{audio_folder}/{pdf_base}.wav' target='_blank'>WAV</a> <a href='{audio_folder}/{pdf_base}.ogg' target='_blank'>OGG</a>")
        
            else:
                result.append(f"<b>{pdf_base}</b> - <i>{pdf_file_num_pages}</i> pages: No audio files found")

        return result

    except Exception as e:
        print(f"An unexpected error occurred in list_audio_files: {e}")
        return []

def delete_file_and_audio_folder(folder_path, filename):
    try:
        file_path = os.path.join(folder_path, filename)
        audio_folder_path = os.path.join(folder_path, f"{filename}-audio")

        result_message = ""

        if os.path.exists(file_path):
            os.remove(file_path)
            result_message += f"File <b>{filename}</b> deleted.\n"
        else:
            result_message += f"File <b>{filename}</b> not found.\n"

        if os.path.exists(audio_folder_path) and os.path.isdir(audio_folder_path):
            # If the "-audio" folder exists, delete it and its contents
            for root, dirs, files in os.walk(audio_folder_path, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir_name in dirs:
                    os.rmdir(os.path.join(root, dir_name))
            os.rmdir(audio_folder_path)
            result_message += f"Audio folder <b>{filename}-audio</b> and its contents deleted."
        else:
            result_message += f"Audio folder <b>{filename}-audio</b> not found."

        return result_message

    except PermissionError:
        return "Error: Permission denied for folder or file."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def backup_folder(source_folder, destination_folder):
    try:
        # Check if the source folder exists
        if not os.path.exists(source_folder):
            raise FileNotFoundError(f"Source folder '{source_folder}' does not exist.")

        # Get the current date
        today_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Modify the destination folder name with the current date
        destination_folder_with_date = f"{destination_folder}-{today_date}"


        # Copy the contents of the source folder to the modified destination folder
        shutil.copytree(source_folder, os.path.join(destination_folder_with_date, os.path.basename(source_folder)))

        # Return a success message
        return f"Backup completed successfully: -> {destination_folder_with_date}"

    except Exception as e:
        # Handle any errors that may occur during the operation
        return f"Error during backup: {e}"

def remove_folder(folder_path):
    try:
        # Check if the folder exists
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder '{folder_path}' does not exist.")

        # Remove the folder and its contents
        shutil.rmtree(folder_path)

        # Return a success message
        return f"Folder and its contents removed successfully: {folder_path}"

    except Exception as e:
        # Handle any errors that may occur during the operation
        return f"Error during folder removal: {e}"


class ConvertParser(BaseBlobParser, ABC):
    
    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        
        original_filename = blob.source
        if original_filename.endswith(".bin"):
            original_filename = original_filename[:-4]
        
        if not os.path.exists(pdf_data_dir):
            os.makedirs(pdf_data_dir)

        file_to_convert_path = os.path.join(pdf_data_dir, original_filename)

        with blob.as_bytes_io() as file:
            # Extract bytes from BytesIO object
            text_bytes = file.getvalue()

        # Write the content to the pdf file in pdf_data_dir
        with open(file_to_convert_path, "wb") as pdf_file:
            pdf_file.write(text_bytes)
        
        yield Document(page_content="original_filename", metadata={"source": original_filename})
       


@hook
def rabbithole_instantiates_parsers(file_handlers: dict, cat) -> dict:

    new_handlers = {
        "application/octet-stream": ConvertParser(),
        # Add other file extensions and corresponding parsers as needed
    }

    file_handlers = file_handlers | new_handlers
    return file_handlers

@hook(priority=7)
def agent_fast_reply(fast_reply, cat) -> Dict:
    return_direct = False
    # Get user message
    user_message = cat.working_memory["user_message_json"]["text"]

    if user_message.startswith("pdf2mp3"):
        check_ffmpeg_installation()

        # Split user_message into two strings
        _, *args = user_message.split(maxsplit=1)

        if args:
            if args[0] == "list":
                audio_file_list = list_audio_files(pdf_data_dir)
                if audio_file_list != []:
                    response = "\n".join(audio_file_list)
                    return {"output": response}
                else:
                    return {"output": "No audio files available"}

            if args[0].startswith("remove"):
                _, *subargs = args[0].split(maxsplit=1)
                if subargs:
                    result_message = delete_file_and_audio_folder(pdf_data_dir, subargs[0])
                    return {"output": result_message}
                else:
                    return {"output": "Please, type a <b>pdf-file.pdf</b> to be removed: <i>pdf2mp3 remove <b>pdf-file.pdf</b></i>"}

            if args[0] == "backup":
                return {"output": backup_folder(pdf_data_dir, "/app/cat/data/pdftoaudio")}

            if args[0] == "cleanup":
                return {"output": remove_folder(pdf_data_dir)}

            if args[0].startswith("-p:"):
                parameter, *subargs = args[0].split(maxsplit=1)
                
                # Extracting the page numbers part
                pages_part = parameter[len("-p:"):]

                # Splitting the range into individual page numbers
                page_numbers = pages_part.split(':')

                if len(page_numbers) == 2 and all(page.isdigit() for page in page_numbers):
                    start_page = int(page_numbers[0])
                    end_page = int(page_numbers[1])
                else:
                    return {"output": "Invalid usage of -p parameter. Pages must be integers: <i>pdf2mp3 -p:<b>1:5</b> pdf-file.pdf</i>"}

                if subargs:
                    # Extracting the filename
                    pdf_filename_to_convert = subargs[0]
                    response = do_convert_pdf_to_audio(pdf_filename_to_convert, cat, start_page=start_page, end_page=end_page)
                    return {"output": response}
                else:
                    return {"output": "Please, type a <b>pdf-file.pdf</b> to be converted: <i>pdf2mp3 -p:1:5 <b>pdf-file.pdf</b></i>"}


            pdf_filename_to_convert = args[0]
            response = do_convert_pdf_to_audio(pdf_filename_to_convert, cat)
            return_direct = True
        else:
            pdf_files_available = str(find_pdf_files(pdf_data_dir, only_not_converted = True))
            if len(pdf_files_available) >= 2:
                pdf_files_available = pdf_files_available[1:-1]
            response = f"<b>How to convert a PDF file to Audio:</b><br>1.<b>Rename</b> your <i>pdf-file.pdf</i> to <i>pdf-file<b>.pdf.bin</b></i><br>2.<b>Upload</b> the <i>pdf-file<b>.pdf.bin</b></i> via <b>Upload file</b><br>3.<b>Type:</b> <i>pdf2mp3 pdf-file<b>.pdf</b></i><br>{pdf_files_available}<br><b>Type:</b> <i>pdf2mp3 <b>-p:3:5</b> pdf-file<b>.pdf</b></i> - to convert only pages from 3 to 5 from the file.<br><b>Type:</b> <i>pdf2mp3 <b>list</b></i> - to download your audio files<br><b>Type:</b> <i>pdf2mp3 <b>backup</b></i> - to backup your audio collection to the cat/data folder<br><b>Type:</b> <i>pdf2mp3 <b>remove</b> pdf-file<b>.pdf</b></i> - to remove the <b>file and its audio collection</b><br><b>Type:</b> <i>pdf2mp3 <b>cleanup</b></i> - to remove <b>all your audio collection</b>. <b>No</b> questions asked!"
            return_direct = True


    # Manage response
    if return_direct:
        return {"output": response}

    return fast_reply