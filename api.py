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
    
def get_cost(page, fil, dic, key = None):
    if key == None:
        key = fil.lower().replace(" ", "_")
    
    try:
        el = page.elements.filter_by_text_contains(fil).extract_single_element()

        price = page.elements.to_the_right_of(el).extract_single_element().text()
        if "-" not in price:
            price = price[1:].replace(",", '')
        else:
            price = "-" + price[2:].replace(",", '')
        
        dic[key] = float(price)
    except:
        dic[key] = None
    
    return dic


def get_invoice(page):
    invoice = {}
    invoice_text = page.elements.filter_by_text_contains("INVOICE :").extract_single_element().text()
    pt = invoice_text.split(" ")[2]

    invoice["policy_type"] = pt
    invoice["policy_number"] = invoice_text.split(" ")[5]
    invoice.update(get_cost(page, f"Total Premium - {pt}", {}, "total_premium"))
    invoice.update(get_cost(page, "Uninsured/Underinsured Motorists/Property Damage", {}, "umpd"))
    invoice.update(get_cost(page, "Medical Payment", {}))
    invoice.update(get_cost(page, "Policy Fee", {}))
    invoice.update(get_cost(page, "Underwriting", {}, "underwriting_fee"))
    invoice.update(get_cost(page, "Surplus Lines Taxes", {}, "sl_tax"))
    invoice.update(get_cost(page, "Stamping Fee", {}))
    invoice.update(get_cost(page, "Maintenance Assessment Fee", {}))
    invoice.update(get_cost(page, "Total Policy Cost", {}))
    invoice.update(get_cost(page, f"Commission - {pt}", {}, "commission"))

    return invoice 

def readpdf(file):
    filename = str(uuid.uuid1())
    with open(f'{filename}.pdf', 'wb') as f:
        f.write(file.file.read())

    try:
        response = {}
        pdf = load_file(f"{filename}.pdf")
        os.remove(f"{filename}.pdf")

        sub_sum = get_cost(pdf.get_page(2), "Total Submission Cost", {})
        total_com = get_cost(pdf.get_page(2), "Total Commission", {})
        sub_sum.update(total_com)
        total_broker = get_cost(pdf.get_page(2), "Total Broker/Service Fees", {}, "total_service_fee")
        sub_sum.update(total_broker)

        response["submission_summary"] = sub_sum
        invoices = []

        for page in pdf.pages:
            try:
                invoice = get_invoice(page)
                invoices.append(invoice)
            except:
                pass
        response["invoices"] = invoices
        return Response(content=json.dumps(response), media_type="application/json")
    except:
        os.remove(f"{filename}.pdf")
        raise HTTPException(status_code=422, detail="PDF Not suitable to the parser")

    

    