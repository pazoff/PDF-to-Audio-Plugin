import os
import subprocess
import PyPDF2
from pydub import AudioSegment
from typing import Dict
from cat.mad_hatter.decorators import tool, hook
from cat.log import log
import threading


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


def convert_pdf_to_audio(pdf_input_filename: str, output_wav_filename: str, output_mp3_filename: str,
                         output_text_filename: str, selected_voice: str,
                         first_pdf_page: int, last_pdf_page: int, cat):
    # Text to speech command
    mimic_cmd = ["mimic3", "--cuda"]

    # Selected voice
    if selected_voice not in ["1", "2", "3", "4", "5", "6", "7"]:
        selected_voice = "5"
    if selected_voice == "2":
        mimic_cmd.append("--voice")
        mimic_cmd.append("en_US/ljspeech_low")
    if selected_voice == "3":
        mimic_cmd.append("--voice")
        mimic_cmd.append("en_US/hifi-tts_low")
        mimic_cmd.append("--speaker")
        mimic_cmd.append("6097")
    if selected_voice == "4":
        mimic_cmd.append("--voice")
        mimic_cmd.append("en_US/hifi-tts_low")
        mimic_cmd.append("--speaker")
        mimic_cmd.append("92")
    if selected_voice == "5":
        mimic_cmd.append("--voice")
        mimic_cmd.append("en_US/vctk_low")
        mimic_cmd.append("--speaker")
        mimic_cmd.append("p303")
    if selected_voice == "6":
        mimic_cmd.append("--voice")
        mimic_cmd.append("en_US/cmu-arctic_low")
        mimic_cmd.append("--speaker")
        mimic_cmd.append("aew")
    if selected_voice == "7":
        mimic_cmd.append("--voice")
        mimic_cmd.append("en_US/hifi-tts_low")
        mimic_cmd.append("--speaker")
        mimic_cmd.append("6097")


    # Read the contents of each page
    pdf_file = open(pdf_input_filename, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    pdf_pages = len(pdf_reader.pages)
    if int(last_pdf_page) == -1:
        last_pdf_page = pdf_pages
    print("Processing the PDF(pages from " + str(first_pdf_page) + " to " + str(
        last_pdf_page) + "), extracting and formatting the text ...")
    cat.send_ws_message(content="Processing the PDF (pages from " + str(first_pdf_page) + " to " + str(
        last_pdf_page) + "), extracting and formatting the text ...", msg_type='chat')

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
        print("Estimated completion time: " + str(
            int((os.path.getsize(output_text_filename) * 0.003594915) * 100) / 100) + " seconds = " + str(
            int((os.path.getsize(output_text_filename) * 0.003594915 / 60) * 100) / 100) + " minutes = " + str(
            int((os.path.getsize(output_text_filename) * 0.003594915 / 3600) * 100) / 100) + " hours.")
        cat.send_ws_message(content="Estimated completion time: " + str(
            int((os.path.getsize(output_text_filename) * 0.003594915) * 100) / 100) + " seconds = " + str(
            int((os.path.getsize(output_text_filename) * 0.003594915 / 60) * 100) / 100) + " minutes = " + str(
            int((os.path.getsize(output_text_filename) * 0.003594915 / 3600) * 100) / 100) + " hours.", msg_type='chat')

        # Generate the speech audio
        # Open the text file
        read_text_file = open(output_text_filename, "r")
        # Open the wav file
        save_wav_file = open(output_wav_filename, "wb")

        # Print mimic commands
        m_cmd = ""
        for cmd in mimic_cmd:
            m_cmd += (cmd + " ")
        print("\n* Executing: " + m_cmd + " < " + output_text_filename + " > " + output_wav_filename + "\n")

        # Execute mimic3 conversion

        subprocess.run(mimic_cmd, stdin=read_text_file, stdout=save_wav_file)

        # Close the wav and txt files
        save_wav_file.close()
        read_text_file.close()

    # Convert the wav file to mp3 and ogg
    if os.path.exists(output_wav_filename):
        if os.path.getsize(output_wav_filename) > 0:
            # Convert to mp3
            print("\n* Converting " + output_wav_filename + " file to " + output_mp3_filename + " ...")
            AudioSegment.from_wav(output_wav_filename).export(output_mp3_filename, format="mp3",
                                                              bitrate="320")
            print("Done.")
            cat.send_ws_message(content=f'<b>{output_mp3_filename}</b> is ready.', msg_type='chat')
            # Convert to ogg
            print("\n* Converting " + output_wav_filename + " file to " + output_mp3_filename[
                                                                          :(len(output_mp3_filename) - 4)] + ".ogg ...")
            AudioSegment.from_wav(output_wav_filename).export(
                output_mp3_filename[:(len(output_mp3_filename) - 4)] + ".ogg", format="ogg")
            print("Done.")

    # Close the PDF file
    pdf_file.close()

# End of convert_pdf_to_audio()

def do_convert_pdf_to_audio(pdf_file_name, cat):
    filepath = "/app/cat/static/pdftomp3/" + pdf_file_name

    if not os.path.exists(filepath):
        print(f"The file {pdf_file_name} does not exist in cat/static/pdftomp3 folder!")
        #cat.send_ws_message(content=f"The file {pdf_file_name} does not exist.", msg_type='chat')
        return f"The file cat/static/pdftomp3/<b>{pdf_file_name}</b> does NOT exist."

    # Specify the folder path
    folder_path = filepath + "-audio"

    # Check if the folder exists, create it if not
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    wav_file_name = folder_path+"/"+pdf_file_name+".wav"
    mp3_file_name = folder_path+"/"+pdf_file_name+".mp3"
    txt_file_name = folder_path+"/"+pdf_file_name+".txt"

    
    tr = threading.Thread(target=convert_pdf_to_audio, args=(filepath, wav_file_name, mp3_file_name, txt_file_name, "5", 1, -1, cat))
    tr.start()
    return f"Converting <b>{pdf_file_name}</b> to audio in the background. You can continue using the Cat ..."

@hook(priority=7)
def agent_fast_reply(fast_reply, cat) -> Dict:
    return_direct = False
    # Get user message
    user_message = cat.working_memory["user_message_json"]["text"]

    if user_message.startswith("pdftomp3"):
        check_ffmpeg_installation()
        if len(user_message.split()) >= 2:
            pdf_filename_to_convert = user_message.split(" ")[1] 
            response = do_convert_pdf_to_audio(pdf_filename_to_convert, cat)
            return_direct = True
        else:
            response = "<b>Usage:</b> pdftomp3 filename.pdf<br>filename.pdf must be in cat/static/pdftomp3 folder!"
            return_direct = True


    # Manage response
    if return_direct:
        return {"output": response}

    return fast_reply