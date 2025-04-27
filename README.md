# PDF to Audio Cat
Turn ★ into ⭐ (top-right corner) if you like the project!

<a href="https://www.buymeacoffee.com/pazoff" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 190px !important;" ></a>

⚠️ https://github.com/remsky/Kokoro-FastAPI have to be installed to use the new version (0.2.0) of this plugin with Kokoro TTS.

* Visit the [Discord Channel](https://discord.com/channels/1092359754917089350/1354320653494386698) for more information.

<img width="50%" src="https://raw.githubusercontent.com/pazoff/PDF-to-Audio-Plugin/main/logo-pdf-to-mp3-cat.jpg">

PDF to Audio Cat plugin for your [Cheshire cat](https://github.com/cheshire-cat-ai/core) involves converting text content in PDF files into audio (MP3,OGG,WAV), enabling you to listen to the document instead of reading it.

<a href="https://github.com/pazoff/PDF-to-Audio-Plugin/raw/main/audio/sample-Snow-white.pdf.mp3" target="_blank">Sample English</a>

<a href="https://github.com/pazoff/PDF-to-Audio-Plugin/raw/main/audio/sample-rus.mp3" target="_blank">Sample Russian</a>

<a href="https://github.com/pazoff/PDF-to-Audio-Plugin/raw/main/audio/sample-it.pdf.mp3" target="_blank">Sample Italian</a>

## How to use it?
Download the <b>PDF-to-Audio-Plugin</b> folder into the <b>cat/plugins</b> one.

<b>How to convert a PDF file to Audio:</b><br>1.<b>Rename</b> your <i>pdf-file.pdf</i> to <i>pdf-file<b>.pdf.bin</b></i><br>2.<b>Upload</b> the <i>pdf-file<b>.pdf.bin</b></i> via <b>Upload file</b><br>3.<b>Type:</b> <i>pdf2mp3 pdf-file<b>.pdf</b></i><br><br><b>Type:</b> <i>pdf2mp3 <b>-p:3:5</b> pdf-file<b>.pdf</b></i> - to convert only pages from 3 to 5 from the file.<br><b>Type:</b> <i>pdf2mp3 <b>list</b></i> - to download your audio files<br><b>Type:</b> <i>pdf2mp3 <b>backup</b></i> - to backup your audio collection to the cat/data folder<br><b>Type:</b> <i>pdf2mp3 <b>remove</b> pdf-file<b>.pdf</b></i> - to remove the <b>file and its audio collection</b><br><b>Type:</b> <i>pdf2mp3 <b>cleanup</b></i> - to remove <b>all your audio collection</b>. <b>No</b> questions asked!

Conversion of PDFs with too many pages (>200) could be resource intensive task and can take a long time, depending on your hardware!


### Example:
<img width="85%" src="https://raw.githubusercontent.com/pazoff/PDF-to-Audio-Plugin/725a5015923d75360d0328f478017b437570e61e/pdf-to-mp3-cat.png">


<img width="85%" src="https://raw.githubusercontent.com/pazoff/PDF-to-Audio-Plugin/main/img/step-1.png">


<img width="85%" src="https://raw.githubusercontent.com/pazoff/PDF-to-Audio-Plugin/main/img/step-2.png">


Updated to version 0.0.3:
Added functions to manage the audio collection

<img width="85%" src="https://raw.githubusercontent.com/pazoff/PDF-to-Audio-Plugin/main/img/1-pdf2mp3.png">

  
<b>pdf2mp3 list</b> to download your audio files

  
<img width="85%" src="https://raw.githubusercontent.com/pazoff/PDF-to-Audio-Plugin/main/img/2-pdf2mp3-list.png">

  
<b>pdf2mp3 remove pdf-file.pdf</b> to remove the file and its audio collection

  
<img width="85%" src="https://raw.githubusercontent.com/pazoff/PDF-to-Audio-Plugin/main/img/3-pdf2mp3-remove.png">

Added Reader selection in the plugin settings
    
<img width="85%" src="https://raw.githubusercontent.com/pazoff/PDF-to-Audio-Plugin/main/img/4-reader-select.png">


