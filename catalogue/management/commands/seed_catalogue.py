from django.core.management.base import BaseCommand
from catalogue.models import Brand, Product

SPECS={
 "Phone (3a) Lite":{"OS":"Nothing OS 3.5","Processor":"MediaTek Dimensity 7300 Pro 5G","Display":"6.77in 120Hz AMOLED","Battery":"5000mAh, 30W wired","Rear camera":"50MP + 8MP + 2MP","Front camera":"16MP","Unlock":"Face and fingerprint"},
 "Phone (4B)":{"OS":"Nothing OS 4.1","Processor":"Snapdragon 6 Gen 4","Display":"6.77in Samsung AMOLED","Battery":"6000mAh India, 33W wired","Rear camera":"50MP + 8MP","Front camera":"16MP","SIM":"Dual nano SIM"},
 "Phone (4A)":{"OS":"Nothing OS 4.1","Processor":"Snapdragon 7s Gen 4","Display":"6.78in 120Hz 1.5K, 4500 nits","Battery":"5400mAh India, 50W","Rear camera":"50MP + 50MP + 8MP","Front camera":"32MP","Zoom":"Up to 70x"},
 "Phone (4A Pro)":{"OS":"Nothing OS 4.1","Processor":"Snapdragon 7 Gen 4","Display":"6.83in 144Hz 1.5K, 5000 nits","Battery":"5400mAh India, 50W","Rear camera":"50MP + 50MP + 8MP","Front camera":"32MP","Zoom":"Up to 140x"},
 "Phone 3":{"OS":"Nothing OS 3.5","Processor":"Snapdragon 8s Gen 4","Display":"6.67in 120Hz AMOLED","Battery":"5150mAh, 65W wired, 15W wireless","Rear camera":"50MP triple camera","Front camera":"50MP","SIM":"Dual nano SIM and eSIM"},
}
NOTHING=[("Phone (3a) Lite","8/128","Nothing Phone (3a) Lite 8GB/128GB","Black / White / Blue",26879,27999),("Phone (3a) Lite","8/256","Nothing Phone (3a) Lite 8GB/256GB","Black / White / Blue",28799,29999),("Phone (4B)","8/128","Nothing Phone (4B) 8GB/128GB","Black / White / Blue",38399,39999),("Phone (4B)","8/256","Nothing Phone (4B) 8GB/256GB","Black / White / Blue",39359,40999),("Phone (4A)","8/128","Nothing Phone (4A) 8GB/128GB","Black / White / Blue / Pink / Yellow",43199,44999),("Phone (4A)","8/256","Nothing Phone (4A) 8GB/256GB","Black / White / Blue / Pink / Yellow",47999,49999),("Phone (4A)","12/256","Nothing Phone (4A) 12GB/256GB","Black / White / Blue / Pink / Yellow",48959,50999),("Phone (4A Pro)","8/128","Nothing Phone (4A) Pro 8GB/128GB","Black / Silver / Pink",52799,54999),("Phone (4A Pro)","8/256","Nothing Phone (4A) Pro 8GB/256GB","Black / Silver / Pink",55679,57999),("Phone (4A Pro)","12/256","Nothing Phone (4A) Pro 12GB/256GB","Black / Silver / Pink",57599,59999),("Phone 3","12/256","Nothing Phone (3) 12GB/256GB","Black / White",76799,79999),("Phone 3","16/512","Nothing Phone (3) 16GB/512GB","Black / White",86399,89999)]
HEIM=[("32HDWLUP","HEIM 32in QLED Whale TV",13490,14990,{"Screen size":"32 inches","Display":"QLED","Series":"Whale","Product type":"Television"}),("32HQLGGW","HEIM 32in HD QLED TV",15490,16990,{"Screen size":"32 inches","Resolution":"HD","Display":"QLED","Product type":"Television"}),("32HQPGGW","HEIM 32in QLED Pro TV",15990,17490,{"Screen size":"32 inches","Display":"QLED Pro","Product type":"Television"}),("43FHATJP","HEIM 43in QLED Android TV",21490,23990,{"Screen size":"43 inches","Display":"QLED","Operating system":"Android TV","Product type":"Television"}),("65HQPGGW","HEIM 65in QLED Pro TV",54990,59990,{"Screen size":"65 inches","Display":"QLED Pro","Product type":"Television"})]

class Command(BaseCommand):
    help="Load verified Nothing and HEIM products with specifications"
    def handle(self,*args,**kwargs):
        nothing,_=Brand.objects.update_or_create(slug="nothing",defaults={"name":"Nothing","logo_text":"NOTHING","sort_order":1})
        heim,_=Brand.objects.update_or_create(slug="heim",defaults={"name":"HEIM","logo_text":"HEIM","sort_order":2})
        for model,variant,description,colours,price,mrp in NOTHING:
            specifications=dict(SPECS[model]); specifications["Capacity"]=variant.replace("/","GB / ")+"GB"
            Product.objects.update_or_create(brand=nothing,model=model,variant=variant,defaults={"description":description,"selling_price":price,"mrp":mrp,"category":"Phones","colours":colours,"specifications":specifications,"is_active":True})
        for model,description,price,mrp,specifications in HEIM:
            Product.objects.update_or_create(brand=heim,model=model,variant="",defaults={"description":description,"selling_price":price,"mrp":mrp,"category":"Televisions","specifications":specifications,"is_active":True})
        self.stdout.write(self.style.SUCCESS("Loaded 17 catalogue products with specifications."))
