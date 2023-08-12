from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
import requests
import json
from django.conf import settings
import random

def index(request):
    return render(request, "qp.html", {'step': 'fetch'})#,{'users': users})
    pass 

def qp_submit(req):
    if req.method!="POST":
        return HttpResponseRedirect(reverse("index"))
    else:
        alabel = req.POST.get('saction')
        if alabel == 'Fetch':
            accid = req.POST.get("accid")
            serviceflag = req.POST.get ("serviceflag","0")
            print ("Action Label = {0}, Accnt Id {1}, ServiceId Flag {2}".format (alabel, accid, serviceflag))
            if accid == None or not accid.strip():
                messages.error(req,"Account id is empty or invalid")
                return HttpResponseRedirect(reverse('index'))

            try:
                url = settings.URL_BILL_SUMMARY.format (accid)
                if serviceflag == "0":
                    url += "&fields=billSummary"
                else:
                    url += "&fields=billSummary,serviceInventory"
                print ("Request URL {}".format (url))
                response = requests.get(url)
                print ("Request response {}".format (response.status_code))
                if response.status_code == 404:
                    messages.error (req, "Bill Summary not found for account [{}]".format (accid))
                    return HttpResponseRedirect(reverse('index'))
                elif response.status_code != 200:
                    messages.error (req, "Unexpected response {} from CustomerBillManagement module".format (response.status_code))
                    return HttpResponseRedirect(reverse('index'))

#                print (response.text)
                bill = response.json()

                print (bill)
                return render(req, "qp.html", {'step': 'show', 'billsummary':bill})
            except Exception as error:
                messages.error(req,"Error fetching bill summary: {0}".format (error))
                return HttpResponseRedirect(reverse('index'))                
        elif alabel == "Confirm Pay":
            accid = req.POST.get("accid")
            if accid == None or not accid.strip():
                messages.error(req,"Account id is empty or invalid")
                return HttpResponseRedirect(reverse('index'))
            
            paymentAmount = req.POST.get("paymentAmount")
            if paymentAmount == None or not paymentAmount.strip() or not paymentAmount.replace('.','',1).isdigit():
                messages.error(req,"Payment amount is empty or invalid")
                return HttpResponseRedirect(reverse('index'))

            paymentMethod = req.POST.get("paymentMethod")
            if paymentMethod == None or not paymentMethod.strip():
                messages.error(req,"Payment method is empty or invalid")
                return HttpResponseRedirect(reverse('index'))

            partyName = req.POST.get("partyName","NoName")
            paymentUnit = req.POST.get("paymentUnit","AED")
            
            print ("Received payment: Account ID {0}, Payment Method {1}, amount {2}".format (accid, paymentMethod, paymentAmount))
            paymentId = random.getrandbits(64)

            account = {
                "id": accid,
                "href": "https://host:port/accountManagement/v4/account/" + accid,
                "name": partyName,
                "description": partyName,
                "@referredType": "PartyAccount",
            }
            totalAmount = {
                "unit": paymentUnit,
                "value": float (paymentAmount),
            }
            paymentMethod = {
                "@type": paymentMethod,
                "description": paymentMethod + " payment",
            }
            payment = {
                "@type": "Payment",
                "name": "WebAssembly Canvas",
                "description": "WebAssembly Canvas payment example", 
                "externalId":  str (paymentId),
                "id" : "",
                "href": "",
                "account": account,
                "totalAmount":totalAmount,
                "paymentMethod":paymentMethod,
            }

            payment_json = json.dumps(payment)
            print (payment_json)
            # Post the payment to wasmcloud actor
            try:
                response = requests.post (settings.URL_POST_PAYMENT,data=payment_json)
                if response.status_code != 200:
                    messages.error (req, "Payment Posting Failure [{} {}]".format (response.status_code, response.text))
                    return HttpResponseRedirect(reverse('index'))   

                print (response.text)
                payment = response.json()

                print (payment)
                messages.success (req, "Payment Posted Successfully")
                return render(req, "qp.html", {'step': 'confirmation', 'payment':payment})
            except Exception as error:
                messages.error(req,"Error fetching bill summary: {0}".format (error))
                return HttpResponseRedirect(reverse('index'))                

        elif alabel == "Restart":
            return HttpResponseRedirect(reverse('index'))        
          
        else:
            messages.error(req,"Unsupported action '{0}'".format (alabel))
            return HttpResponseRedirect(reverse('index'))        
