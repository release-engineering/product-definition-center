# 1. Automated build: 
# https://hub.docker.com/r/lao605/product-definition-center/builds/
# 
########################################### 
# Guide:
# 1. Use this to build a new image
# docker build -t <YOUR_NAME>/pdc <the directory your Dockerfile is located>
# 
# 2. Running the container
# 	2.1 To display the log interactively (with a terminal)
# 	docker run -it -P -v $PWD:$PWD <YOUR_NAME>/pdc python $PWD/manage.py runserver 0.0.0.0:8000
# 
# 	2.2 To run the container in daemon mode
# 	docker run -d -P -v $PWD:$PWD <YOUR_NAME>/pdc python $PWD/manage.py runserver 0.0.0.0:8000
# 
# 
# 3. Check the addresses
# 	3.1 Check the address of the docker machine
# 	*For Mac OS or Windows Users*
# 		docker-machine env <the name of your docker machine> --> DOCKER_HOST
# 	
# 	*For Linux Users*
# 		docker inspect <container_id> | grep IPAddress | cut -d '"' -f 4 --> DOCKER_HOST
# 
# 	3.2 Check the mapped port of your running container
# 	docker ps -l --> PORTS
# 
# 4. Access it
# visit <DOCKER_HOST:PORTS> on your web browser
# 
# 5. Edit code and see changes
# save after editing code in your $PWD directory and see changes will happen in the container (changes need more time to take effect than in local env)

FROM fedora:21
MAINTAINER Zhikun Lao <zlao@redhat.com>

LABEL Description = "product-definition-center"
LABEL Vendor = "Fedora"
LABEL Version = "0.5"

# patternfly1
RUN curl https://copr.fedoraproject.org/coprs/patternfly/patternfly1/repo/fedora-21/patternfly-patternfly1-fedora-21.repo > /etc/yum.repos.d/patternfly-patternfly1-fedora-21.repo
RUN curl http://www.graphviz.org/graphviz-rhel.repo > /etc/yum.repos.d/graphviz-rhel.repo

# solve dependencies
RUN yum -y upgrade && yum install -y \
rpm-build \
sudo \
passwd \
tar \
git \
make \
gcc \
libuuid-devel \
python-devel \
python-setuptools \
python-pip swig \
openldap-devel \
krb5-devel \
koji \
patternfly1 \
vim-enhanced \
'graphviz*' \
libxml2 \
libxslt \
libxml2-devel \
libxslt-devel \
# openssh-server \
net-tools \
; yum clean all

RUN echo "123" | passwd root --stdin

COPY requirements /tmp/requirements/
RUN pip install -r /tmp/requirements/devel.txt

# RUN echo "Port 22" >> /etc/ssh/sshd_config
# RUN echo "ListenAddress 0.0.0.0" >> /etc/ssh/sshd_config
# RUN ssh-keygen -A
# RUN systemctl enable sshd.service

# EXPOSE 8000 22
EXPOSE 8000

CMD ["/bin/bash"]