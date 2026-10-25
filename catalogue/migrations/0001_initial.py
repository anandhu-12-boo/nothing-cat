from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[
        migrations.CreateModel(name="Brand",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("name",models.CharField(max_length=60,unique=True)),("slug",models.SlugField(unique=True)),("logo_text",models.CharField(blank=True,max_length=30)),("sort_order",models.PositiveIntegerField(default=0)),("is_active",models.BooleanField(default=True))],options={"ordering":["sort_order","name"]}),
        migrations.CreateModel(name="Product",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("model",models.CharField(max_length=120)),("variant",models.CharField(blank=True,max_length=100)),("description",models.CharField(max_length=240)),("selling_price",models.DecimalField(decimal_places=2,max_digits=12)),("mrp",models.DecimalField(decimal_places=2,max_digits=12)),("category",models.CharField(default="Phones",max_length=80)),("colours",models.CharField(blank=True,max_length=220)),("specifications",models.JSONField(blank=True,default=dict)),("stock",models.PositiveIntegerField(default=0)),("is_active",models.BooleanField(default=True)),("updated_at",models.DateTimeField(auto_now=True)),("brand",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="products",to="catalogue.brand"))],options={"ordering":["brand__sort_order","selling_price","model"]}),
        migrations.AddConstraint(model_name="product",constraint=models.UniqueConstraint(fields=("brand","model","variant"),name="unique_brand_model_variant")),
    ]

