import setuptools

setuptools.setup(
    name="uma_mobile",
    version="1.0.0",
    description="UMA MikroTik User Manager Mobile App",
    author="UMA Team",
    author_email="info@uma.com",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'toga',
        'paramiko'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
