FROM public.ecr.aws/lambda/python:3.10

COPY preprocessing_list.py preprocessing_utils.py preprocessor.py  references.py ./

COPY app.py requirements.txt ./

RUN python3.8 -m pip install -r requirements.txt -t .

# RUN python3.8 -m pip install torch==1.10.0+cpu torchvision==0.11.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html -t .

RUN yum install -y mesa-libGL

# Command can be overwritten by providing a different command in the template directly.
CMD ["app.lambda_handler"]
