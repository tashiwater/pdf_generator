echo %~dp0%result.pdf
call  C:\Users\usr\anaconda3\Scripts\activate.bat
python ./scripts/generate_image_pdf.py
%~dp0%result.pdf