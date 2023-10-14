from py_pdf_parser.loaders import load_file
from fastapi import FastAPI, UploadFile, File, Response, HTTPException
import json
import traceback
import uuid
import os


api = FastAPI()


@api.post("/api/v1/tools/coverwhale/invoice-reader")
async def upload_file(file: UploadFile = File(...)):
        ir = invoiceReader()
        return ir.readpdf(file)

@api.post("/api/v1/tools/coverwhale/quote-reader")
async def upload_file(file: UploadFile = File(...)):
        qr = QuoteReader()
        return qr.readpdf(file)
    

class invoiceReader():

    def get_cost(self, page, fil, dic, key = None):
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


    def get_invoice(self, page):
        invoice = {}
        invoice_text = page.elements.filter_by_text_contains("INVOICE :").extract_single_element().text()
        pt = invoice_text.split(" ")[2]

        invoice["policy_type"] = pt
        invoice["policy_number"] = invoice_text.split(" ")[5]
        invoice.update(self.get_cost(page, f"Total Premium - {pt}", {}, "total_premium"))
        invoice.update(self.get_cost(page, "Uninsured/Underinsured Motorists/Property Damage", {}, "umpd"))
        invoice.update(self.get_cost(page, "Medical Payment", {}))
        invoice.update(self.get_cost(page, "Policy Fee", {}))
        invoice.update(self.get_cost(page, "Underwriting", {}, "underwriting_fee"))
        invoice.update(self.get_cost(page, "Surplus Lines Taxes", {}, "sl_tax"))
        invoice.update(self.get_cost(page, "Stamping Fee", {}))
        invoice.update(self.get_cost(page, "Maintenance Assessment Fee", {}))
        invoice.update(self.get_cost(page, "Total Policy Cost", {}))
        invoice.update(self.get_cost(page, f"Commission - {pt}", {}, "commission"))

        return invoice 

    def readpdf(self, file):
        filename = str(uuid.uuid1())
        with open(f'{filename}.pdf', 'wb') as f:
            f.write(file.file.read())

        try:
            response = {}
            pdf = load_file(f"{filename}.pdf")
            os.remove(f"{filename}.pdf")

            sub_sum = self.get_cost(pdf.get_page(2), "Total Submission Cost", {})
            total_com = self.get_cost(pdf.get_page(2), "Total Commission", {})
            sub_sum.update(total_com)
            total_broker = self.get_cost(pdf.get_page(2), "Total Broker/Service Fees", {}, "total_service_fee")
            sub_sum.update(total_broker)

            response["submission_summary"] = sub_sum
            invoices = []

            for page in pdf.pages:
                try:
                    invoice = self.get_invoice(page)
                    invoices.append(invoice)
                except:
                    pass
            response["invoices"] = invoices
            return Response(content=json.dumps(response), media_type="application/json")
        except:
            os.remove(f"{filename}.pdf")
            raise HTTPException(status_code=422, detail="PDF Not suitable to the parser")


class QuoteReader():
    def get_cost_right(self, page, fil, dic, key = None):
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

    def get_cost(self, page, fil, dic, key = None):
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

    def get_carrier(self, page):
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

    def get_invoice(self, page):
        invoice = {}

        invoice.update(self.get_carrier(page))
        invoice.update(self.get_cost(page, "Policy Fee:", {}))
        invoice.update(self.get_cost(page, "Underwriting Fee:", {}))
        invoice.update(self.get_cost(page, "Surplus Lines Tax:", {}))
        invoice.update(self.get_cost(page, "Stamping Fee:", {}))
        invoice.update(self.get_cost(page, "Maintenance Assessment Fees:", {}))
        invoice.update(self.get_cost_right(page, "Premium Subtotal", {}, "premium_subtotal"))

        return {f"Page {page.page_number}": invoice}

    def readpdf(self, file):
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
                    invoice = self.get_invoice(page)
                    invoices.append(invoice)
                except:
                    pass

            response["Quote"] = invoices
            return Response(content=json.dumps(response), media_type="application/json")
        except:
            os.remove(f"{filename}.pdf")
            raise HTTPException(status_code=422, detail="PDF Not suitable to the parser")

    

    