import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-soft-delete",
    version="1.0.11",
    author="Alexander Yudkin",
    author_email="san4ezy@gmail.com",
    description="Soft delete models, managers, queryset for Django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/san4ezy/django_softdelete",
    packages=setuptools.find_packages(
        include=["django_softdelete", "django_softdelete.*"]
    ),
    include_package_data=True,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.6',
)
