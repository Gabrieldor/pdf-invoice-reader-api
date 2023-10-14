from py_pdf_parser.loaders import load_file
import traceback
import json


class a():

    def get_cost_right(self, page, fil, dic, key = None):
        try:
            el = page.elements.filter_by_text_contains(fil).extract_single_element()
            if key == None:
                key = el.text().lower().replace(" ", "_")
                try:
                    print(key)
                    dic["coverage_type"] = key.split("(")[1][:-1]
                    key = key.split("_(")[0]
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
        invoice.update(self.get_cost_right(page, "Premium Subtotal", {}))

        return {f"Page {page.page_number}": invoice} 

    def test(self):
        response = {}
        pdf = load_file("Quote-RONNIE.pdf")
        invoices = []
        for page in pdf.pages:
            try:
                invoice = self.get_invoice(page)
                invoices.append(invoice)
            except:
                pass

        response["Quote"] = invoices
        print(json.dumps(response, indent=4))


tes = a()
tes.test()