from py_pdf_parser.loaders import load_file
from fastapi import FastAPI, UploadFile, File, Response, HTTPException
import json
import traceback
import uuid
import os


api = FastAPI()

@api.post("/api/v1/pdf-to-json")
async def upload_file(file: UploadFile = File(...)):
        return readpdf(file)


def get_cost_right(page, fil, dic, key = None):
    try:
        el = page.elements.filter_by_text_contains(fil).extract_single_element()
        key = el.text().lower().replace(" ", "_")
        try:
            print(key)
            dic["coverage_type"] = key.split("(")[1][:-1]
        except:
            pass


        price = page.elements.to_the_right_of(el).extract_single_element().text()
        if "-" not in price:
            price = price[1:].replace(",", '')
        else:
            price = "-" + price[2:].replace(",", '')
        
        dic[key] = price
    except:
        dic[key] = None
    
    return dic

def get_cost(page, fil, dic, key = None):
    if key == None:
        key = fil.lower().replace(" ", "_")[:-1]
    
    try:
        el = page.elements.filter_by_text_contains(fil).extract_single_element()
        el = el.text()
        price = el.split(":")[1]
        price = price.replace("\n", "")
        dic[key] = price
    except:
        dic[key] = None
    
    return dic

def get_carrier(page):
    key = "Carrier"
    dic = {}
    try:
        el1 = page.elements.filter_by_text_equal(key).extract_single_element()
        el2 = page.elements.filter_by_text_contains("Carrier Rating").extract_single_element()
        el = page.elements.between(el1, el2).extract_single_element().text()
    except:
        pass
    dic[key] = el
    return dic

def get_invoice(page):
    invoice = {}

    invoice.update(get_carrier(page))
    invoice.update(get_cost(page, "Policy Fee:", {}))
    invoice.update(get_cost(page, "Underwriting Fee:", {}))
    invoice.update(get_cost(page, "Surplus Lines Tax:", {}))
    invoice.update(get_cost(page, "Stamping Fee:", {}))
    invoice.update(get_cost(page, "Maintenance Assessment Fees:", {}))
    invoice.update(get_cost_right(page, "Premium Subtotal", {}, "premium_subtotal"))

    return {f"Page {page.page_number}": invoice}

def readpdf(file):
    filename = str(uuid.uuid1())
    with open(f'{filename}.pdf', 'wb') as f:
        f.write(file.file.read())

    try:
        response = {}
        pdf = load_file(f"{filename}.pdf")
        os.remove(f"{filename}.pdf")
        invoices = []
        for page in pdf.pages:
            try:
                invoice = get_invoice(page)
                invoices.append(invoice)
            except:
                pass

        response["Quote"] = invoices
        return Response(content=json.dumps(response), media_type="application/json")
    except:
        os.remove(f"{filename}.pdf")
        raise HTTPException(status_code=422, detail="PDF Not suitable to the parser")

    

    