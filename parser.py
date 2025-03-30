from dotenv import load_dotenv
import os

load_dotenv()
# bring in deps
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader

# set up parser
parser = LlamaParse(
    result_type="markdown"  # "markdown" and "text" are available
)

# use SimpleDirectoryReader to parse our file
file_extractor = {".pdf": parser}
documents = SimpleDirectoryReader(input_files=['DhananjayAgnihotri---Resume.pdf'], file_extractor=file_extractor).load_data()
print(documents)