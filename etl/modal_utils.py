import modal

# definition of our container image for jobs on Modal
# Modal gets really powerful when you start using multiple images!
image = modal.Image.debian_slim(  # we start from a lightweight linux distro
    python_version="3.10"  # we add a recent Python version
).pip_install(  # and we install the following packages:
    "boto3",
    "pandas",
    "requests",
    "python-dotenv",
    "pymongo[srv]",
    "beautifulsoup4"
)

# we define a Stub to hold all the pieces of our app
# most of the rest of this file just adds features onto this Stub
stub = modal.Stub(
    name="nass-etl",
    image=image,
    secrets=[
        # this is where we add API keys, passwords, and URLs, which are stored on Modal
        modal.Secret.from_name("mongodb"),
        modal.Secret.from_name("my-mongodb-secret")
    ],
    mounts=[
        # we make our local modules available to the container
        *modal.create_package_mounts(module_names=["utils/vecstore", "utils/docstore", "utils/utils"])
    ],
)
