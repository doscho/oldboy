from django.shortcuts import HttpResponse, render, redirect
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe


class ModelXadmin(object):
    # 存放要显示哪些字段的列表
    list_display = ["__str__", ]
    list_display_links = []
    model_class = None

    def __init__(self, model, site):
        self.model = model
        self.site = site
    def new_display_list(self):
        """
        新的展示列表，增加了能够点击编辑的数据字段
        :return: 新的展示列表
        """
        temp = []
        temp.append(ModelXadmin.check)
        temp.extend(self.list_display)
        if not self.list_display_links:
            temp.append(ModelXadmin.edit)
        temp.append(ModelXadmin.deletes)
        return temp

    def get_add_url(self):
        """
        返回添加数据的url
        :return:
        """

        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_add"%(app_label, model_name))

        return _url

    def get_list_url(self):
        """
        返回展示数据的url
        :return:
        """

        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_list" % (app_label, model_name))

        return _url

    def get_change_url(self, obj):
        """
        返回编辑数据的url
        :param obj: 要编辑的数据对象
        :return:
        """

        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_change" % (app_label, model_name), args=(obj.pk,))

        return _url

    def get_delete_url(self, obj):
        """
        返回删除数据的url
        :param obj:要删除的数据对象
        :return:
        """

        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_delete" % (app_label, model_name), args=(obj.pk,))

        return _url

    def get_modelform_class(self):
        if not self.model_class:
            from django.forms import ModelForm
            class ModelFormDemo(ModelForm):
                class Meta:
                    model = self.model
                    fields = "__all__"

            return ModelFormDemo
        else:
            return self.model_class


    def edit(self, obj=None, is_header=False):

        # 用在传表头的时候
        if is_header is True:
            return "操作"

        url = self.get_change_url(obj)
        return mark_safe('<a href="'+url+'">编辑</a>')

    def deletes(self, obj=None, is_header=False):

        # 用在传表头的时候
        if is_header is True:
            return "操作"

        url = self.get_delete_url(obj)
        return mark_safe('<a href="'+url+'">删除</a>')

    def check(self, obj=None, is_header=False):

        # 用在传表头的时候
        if is_header is True:
            return mark_safe('<input id="choice" type="checkbox">')
            # return "操作"

        return mark_safe('<input type="checkbox">')


    def list_view(self, request):
        # 所有的数据
        data_list = self.model.objects.all()
        # 数据表的名称
        model_name = self.model._meta.model_name

        # 处理表头
        header_list = []

        # 为list_display的每个字段都添加相应的表头
        for field in self.new_display_list():

            # 字段为数据表自带
            if isinstance(field, str):
                # 默认list_display
                if field == '__str__':
                    val = self.model._meta.model_name.upper()
                else:
                    field_obj = self.model._meta.get_field(field)
                    val = field_obj.verbose_name
            # 字段为自添加函数
            else:
                # is_header判断是否在传表头时调用
                val = field(self, is_header=True)
            header_list.append(val)

        # 处理表单数据的列表
        new_data_list = []

        for data_obj in data_list:
            temp = []
            for field in self.new_display_list():
                # 取数据对象相应的字段
                if isinstance(field, str):
                    val = getattr(data_obj, field)
                    # 如果是根据该字段进入编辑页面
                    if field in self.list_display_links:
                        _url = self.get_change_url(data_obj)
                        val = mark_safe("<a href='%s'>%s</a>" % (_url, val))
                else:
                    val = field(self, data_obj)

                temp.append(val)

            new_data_list.append(temp)

        # 添加url
        add_url = self.get_add_url()
        return render(request,
                      "list_view.html",
                      locals()
                      )

    def add_view(self, request):
        ModelFormDemo = self.get_modelform_class()
        # 从前端传回数据
        if request.method == "POST":
            form = ModelFormDemo(request.POST)
            # 通过校验，保存并返回到查看页面
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())

            # 没通过校验,直接返回到添加页面，此时保留的是填写好的表单
            return render(request, "add_view.html", locals())

        form = ModelFormDemo()

        return render(request, "add_view.html", locals())

    def change_view(self, request, id):
        data_obj = self.model.objects.filter(pk=id).first()
        ModelFormDemo = self.get_modelform_class()
        # 从前端传回数据
        if request.method == "POST":
            form = ModelFormDemo(request.POST, instance=data_obj)
            # 通过校验，保存并返回到查看页面
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())

            # 没通过校验,直接返回到添加页面，此时保留的是填写好的表单
            return render(request, "change_view.html", locals())

        form = ModelFormDemo(instance=data_obj)

        return render(request, "change_view.html", locals())

    def delete_view(self, request, id):
        url = self.get_list_url()

        if request.method == "POST":
            self.model.objects.filter(pk=id).first().delete()
            return redirect(url)

        return render(request, "delete_view.html", locals())

    def get_urls2(self):
        """
        二级分发url函数
        :return: 代表操作url的列表
        """
        temp = []

        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        temp.append(url(r"^add/", self.add_view, name="%s_%s_add" % (app_label, model_name)))
        temp.append(url(r"^(\d+)/delete/", self.delete_view, name="%s_%s_delete" % (app_label, model_name)))
        temp.append(url(r"^(\d+)/change/", self.change_view, name="%s_%s_change" % (app_label, model_name)))
        temp.append(url(r"^$", self.list_view, name="%s_%s_list" % (app_label, model_name)))

        return temp

    @property
    def urls2(self):
        return self.get_urls2(), None, None


class XadminSite(object):
    def __init__(self):
        self._registry = {}

    def get_urls(self):
        temp = []

        for model, admin_class_obj in self._registry.items():
            app_name = model._meta.app_label
            mode_name = model._meta.model_name

            temp.append(url(r'^{}/{}/'.format(app_name, mode_name), admin_class_obj.urls2))
        return temp

    @property
    def urls(self):
        return self.get_urls(), None, None

    def register(self, model, admin_class=None, **options):
        if not admin_class:
            admin_class = ModelXadmin

        self._registry[model] = admin_class(model, self)


site = XadminSite()
