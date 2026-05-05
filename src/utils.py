"""
Module to perform LLM based Document Search
"""
from io import BytesIO
from pydantic import BaseModel, Extra
import pymupdf4llm
import fitz
import re
from PyPDF2 import PdfReader
from typing import List, Mapping
from collections import defaultdict
import numpy as np
import pandas as pd


class Utils():
    """Wrapper for Document Search API."""

    k: int = 10

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def __separate_pages(self, md_text):
        pages = []
        for text in [page.strip() for page in md_text.split("-----\n\n") if page.strip()]:
            if type(text) == bytes:
                text = text.decode('utf-8')
            
            #pages.append(re.sub("\(data:image/.*\)|(<img.*data:image/.*)","",text)) 
            pages.append(re.sub(r"\(data:image/[^)]*\)|<img[^>]*data:image/[^>]*>", "", text))       
        return pages
    
    # @time_after(PymupdfTimeout)
    #@timeout(20,PymupdfTimeout)
    def extract_text_pymupdf(self, document_bytes):
        doc = fitz.open(stream=document_bytes, filetype="pdf")

        # if fr for landscape pages are to be used
        # get all pages
        fr_pages = []
        pymupdf_pages = []
        for i, page in enumerate(doc.pages()):
            #is_landscape = page.rect.width > page.rect.height
            # print(f"page no {i+1} width {page.rect.width}, height {page.rect.height}")

            pymupdf_pages.append(i)

        # pass pages to respective functions

        markdown_text = pymupdf4llm.to_markdown(doc, pages=pymupdf_pages)
        pages = self.__separate_pages(markdown_text)

        output = {index + 1: value for index, value in enumerate(pages)}

    
        return output


    @staticmethod
    def checkFile(file_byte):
        """_Function to check if file is corrupted or not_

        Args:
            file_byte (_byte_): _File bytes_

        Raises:
            ReadPdfError: _Error Object for ReadPdf_

        Returns:
            _exception_: _Exception on PDF reader error_
        """
        try:
            pdf = PdfReader(BytesIO(file_byte))
            info = pdf.metadata
            if not info:
                raise "pdf error"
        except:
            raise "pdf error"
        

    
    def extract_tables(self, doc) -> Mapping:
        """Module to extract tables from the PDF to be vectorized as a unit in subsequent steps

        Parameters:
            - documents: A list of paths to the PDF files whose tables needs to be extracted
        Returns:
            The module list of all the tables within the PDF in markdown format
        """

        all_tables = []
        for table in doc["tables"]:
            # for table in curr_page["tables"]:
            row_count = table["rowCount"]
            column_count = table["columnCount"]
            table_mat = np.full(
                (row_count, column_count), fill_value="placeholder", dtype=object
            )
            for i in table["cells"]:
                table_mat[i["rowIndex"]][i["columnIndex"]] = i["content"]
            table_df = pd.DataFrame(table_mat)
            table_df.columns = table_df.iloc[0]
            table_df.drop(0, inplace=True)
            page_num = table["cells"][0]["boundingRegions"][0]["pageNumber"]
            # dynamically split tables based on split_by_parts value
            # embedding can only take in maximum of ~2K tokens
            # split_by_parts = self.__get_num_splits(table_df)
            # for tempdf in np.array_split(table_df, split_by_parts):
            all_tables.append((page_num, table_df))

        all_tables_markdown = [
            (page_num, table.to_markdown()) for page_num, table in all_tables
        ]
        return all_tables_markdown

    def extract_para(self, doc: dict):
        content_txt = defaultdict(str)
        # no_bb_set = set()
        for para_dict in doc["paragraphs"]:
            page_no = para_dict["boundingRegions"][0]["pageNumber"]

            if "role" in para_dict.keys():
                # {'pageFooter', 'pageNumber', 'sectionHeading', 'title'}

                # no_bb_set.add(len(para_dict['boundingRegions']))
                if para_dict["role"] == "title":
                    content_txt[page_no] += f"<h1>{para_dict['content']}</h1>"
                elif para_dict["role"] == "sectionHeading":
                    content_txt[page_no] += f"<h2>{para_dict['content']}</h2>"
                else:
                    # new_rols_set.add(para_dict["role"])
                    content_txt[page_no] += para_dict["content"]
            else:
                # if len(para_dict['content'].split(' ')) > 3:
                content_txt[page_no] += para_dict["content"]
            content_txt[page_no] += "\n\n"
        return content_txt

    # def __separate_pages(self, md_text):
    #     pages = [page.strip() for page in md_text.split("-----\n\n") if page.strip()]
    #     return pages
