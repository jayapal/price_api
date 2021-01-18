import requests
from io import StringIO

from django.db import models
from django.conf import settings
from django.core.files.base import File


class ProductFamily(models.Model):
    name = models.CharField(max_length=500)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Product Family"
        verbose_name_plural = "Product Familys"
        db_table = 'BrandFavourite_productfamily'


class Department(models.Model):
    name = models.CharField(max_length=500, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        db_table = 'BrandFavourite_department'


class Category(models.Model):
    name = models.CharField(max_length=500, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'BrandFavourite_category'


class SubCategory(models.Model):
    name = models.CharField(max_length=500, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Sub Category"
        verbose_name_plural = "Sub Categorys"
        db_table = 'BrandFavourite_subcategory'


class Route(models.Model):
    product_family = models.ForeignKey(ProductFamily, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    parent = models.BooleanField(default=False)
    lifestyle_photo = models.URLField(max_length=1000, blank=True, null=True)

    def __unicode__(self):
        return str(self.id)+" --- "+str(self.category)+" --- "+str(self.sub_category)
        #return str(self.id)+" -> "+str(self.product_family)+" | "+str(self.department)+" | "+\
              #str(self.category)+" | "+str(self.sub_category)

    class Meta:
        db_table = 'BrandFavourite_route'


class Collections(models.Model):
    name = models.CharField(max_length=500)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Collections"
        verbose_name_plural = "Collections"
        db_table = 'BrandFavourite_collections'


class Tags(models.Model):
    name = models.CharField(max_length=500)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Tags"
        verbose_name_plural = "Tags"
        db_table = 'BrandFavourite_tags'


class MicroTags(models.Model):
    name = models.CharField(max_length=500)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Microtags"
        verbose_name_plural = "Microtags"
        db_table = 'BrandFavourite_microtags'


class Brand(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)
    logo = models.ImageField(upload_to='custompic/',
                                blank=True, null=True)
    website = models.URLField(null=True, blank=True, max_length=1000)
    enable = models.BooleanField(default=False)
    placement = models.IntegerField(null=True, blank=True, max_length=20)
    created_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        db_table = 'BrandFavourite_brand'


#Store Table
class Stores(models.Model):
    USED = '1'
    LOCAL = '2'
    GENERIC = '3'

    VARIANTS = (
        (USED, ('used')),
        (LOCAL, ('local')),
        (GENERIC, ('generic'))
        )

    name = models.CharField(max_length=200, unique=True, db_index=True)
    website = models.URLField(db_index=True)
    display_name = models.CharField(max_length=200, blank=True, null=True)
    program_id = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to='custompic/',
                                blank=True, null=True)
    full_logo = models.ImageField(upload_to='custompic/', blank=True, null=True)
    enable = models.BooleanField(default=False)
    placement = models.IntegerField(null=True, blank=True, max_length=20)
    lifestyle_pic = models.ImageField(upload_to='custompic/',blank=True, null= True)
    fmtc_id = models.IntegerField(blank=True, null=True, db_index=True)
    banner = models.ImageField(upload_to='custompic/', blank=True, null=True)
    is_trending = models.BooleanField(default=False)
    coupilia_merchant_id = models.IntegerField(blank=True, null=True, db_index=True)
    variation_type = models.CharField(blank=True, null=True, max_length=16)
    square_logo = models.ImageField(upload_to='custompic/', blank=True, null=True)
    retailerHandling = models.TextField(blank=True, null=True)

    def __unicode__(self):
        if self.display_name:
            return str(self.display_name)
        return self.name

    class Meta:
        verbose_name = "Stores"
        verbose_name_plural = "Stores"
        db_table = 'BrandFavourite_stores'

    def save(self, *args, **kwargs):
        super(Stores, self).save(*args, **kwargs)
        #self.add_or_update_algolia()
        if not self.logo:
            # Get logo from clearbit if not provided
            self.save_clearbit_logo()

    def save_clearbit_logo(self):
        """ Saves logo from clearbit if not present
        :return: True if logo is already there or updated, False otherwise
        """
        '''if self.logo:
            # Skip if logo is already present
            return True'''

        # Get domain from url
        domain = self.website.replace("http://", "").replace("https://", "").replace("www.", "").replace("/", "")
        if domain:
            logo_file = StringIO()
            try:
                # Get logo from clear bit and save to a file object
                url = "http://logo.clearbit.com/{}".format(domain)
                r = requests.get(url)
                content = r.content
                logo_file.write(content)
                logo_file.size = logo_file.tell()
                extension = r.headers['content-type'].split("/")[1]
                file_name = "{}.{}".format(self.name, extension)
            except Exception as e:
                print("EXCEPTION ", e)
                return False
            else:
                # Add logo file to WhiteListedDomain.
                self.logo.save(file_name, File(logo_file), save=False)
                self.save()

        return True


class ProductsV2(models.Model):

    gender_types = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('unisex', 'Unisex'),
        ('unknown', 'Unknown'),
    )
    # category = models.ForeignKey(Category, null=True, blank=True)
    marketplace_identification_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    product_identification_id = models.CharField(null=True, blank=True, max_length=100, db_index=True)
    title = models.CharField(null=True, blank=True, max_length=200)
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.CASCADE)
    store_name = models.CharField(null=True, blank=True, max_length=500)
    store = models.ForeignKey(Stores, on_delete=models.CASCADE)
    manufacture = models.CharField(null=True, blank=True, max_length=100)
    description = models.TextField(null=True, blank=True)
    upc = models.CharField(null=True, blank=True, max_length=20, db_index=True)
    color = models.CharField(null=True, blank=True, max_length=100)
    color_v2 = models.CharField(null=True, blank=True, max_length=200)
    color_csv = models.CharField(null=True, blank=True, max_length=200)
    department = models.CharField(null=True, blank=True, max_length=100)
    condition = models.CharField(null=True, blank=True, max_length=50)
    currency_code = models.CharField(null=True, blank=True, max_length=100)
    ratings = models.FloatField(null=True, blank=True, max_length=20)
    no_of_reviews = models.IntegerField(null=True, blank=True, max_length=20)
    price = models.FloatField(null=True, blank=True, max_length=20, db_index=True)
    price_sold = models.FloatField(null=True, blank=True, max_length=20, db_index=True)
    min_price = models.FloatField(null=True, blank=True, max_length=20, db_index=True)
    max_price = models.FloatField(null=True, blank=True, max_length=20, db_index=True)
    #avg_price = models.FloatField(null=True, blank=True, max_length=20, db_index=True)

    amount_saved = models.FloatField(null=True, blank=True, max_length=20)
    percentage_saved = models.FloatField(null=True, blank=True, max_length=20, db_index=True)
    purchase_url = models.URLField(null=True, blank=True, max_length=1000, db_index=True)
    # merchant = models.ForeignKey(Merchant, null=True, blank=True)
    is_reviewed = models.BooleanField(default=False)
    is_curated = models.BooleanField(default=False)
    updated_on = models.DateTimeField(auto_now=True)
    order = models.IntegerField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    collection = models.ManyToManyField(Collections, blank=True, null=True)
    tags = models.ManyToManyField(Tags, blank=True, null=True)
    micro_tags = models.ManyToManyField(MicroTags, blank=True, null=True)
    route = models.ManyToManyField(Route, blank=True, null=True)
    size = models.CharField(null=True, blank=True, max_length=50)
    gender = models.CharField(choices = gender_types, default='female', max_length=20)
    sem3_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    sem3_category = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    sem3_cat_id = models.IntegerField(blank=True, null=True, db_index=True)
    coupon_code = models.CharField(max_length=100, blank=True, null=True)
    stock = models.IntegerField(blank=True, null=True)
    data_source = models.IntegerField(choices=settings.PRODUCT_SOURCE, blank=True,
        null=True, db_index=True)

    def __unicode__(self):
        return ('%s - ID: %s') %(self.title, str(self.id))

    class Meta:

        verbose_name = "Product"
        verbose_name_plural = "Products"
        db_table = 'BrandFavourite_productsv2'
