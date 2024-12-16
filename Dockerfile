FROM python:3.11.7-slim

RUN sed -i 's@deb.debian.org@mirrors.ustc.edu.cn@g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y curl git socat && rm -rf /var/lib/apt/lists/*

RUN true && \
    apt-get update && \
    apt-get install -y curl git socat bsdmainutils && \
    rm -rf /var/cache/apt/lists /var/lib/apt/lists/* && \
    true

COPY requirements.txt /tmp/requirements.txt

RUN pip config set global.index-url https://mirrors.ustc.edu.cn/pypi/simple && \
    pip install -r /tmp/requirements.txt

WORKDIR /home/ctf

ENV FOUNDRY_DIR=/opt/foundry
ENV PATH=${FOUNDRY_DIR}/bin/:${PATH}
RUN true && \
    curl -L https://foundry.paradigm.xyz | bash && \
    foundryup && \
    true

COPY . .

RUN cd /home/ctf/challenge/project && forge build --out /artifacts/out --cache-path /artifacts/cache


