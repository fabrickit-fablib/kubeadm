# coding: utf-8

from fabkit import *  # noqa
from fablib.base import SimpleBase


class Kubeadm(SimpleBase):
    def __init__(self, is_master=True):
        self.data_key = 'kubeadm'
        self.data = {
            'kubernetes_version': 'stable-1.6',
            'service_cidr': '10.96.0.0/12',
            'pod_network_cidr': '10.244.0.0/16',
        }
        self.packages = {}
        self.services = {}
        self.is_master = is_master

    def setup(self):
        data = self.init()
        if self.is_ubuntu:
            filer.template('/tmp/bootstrap_ubuntu.sh')
            sudo('sh /tmp/bootstrap_ubuntu.sh')
        elif self.is_centos:
            filer.template('/tmp/bootstrap_centos.sh')
            sudo('sh /tmp/bootstrap_centos.sh')

        if self.is_master:
            sudo('ss -ln | grep LISTEN | grep ":6443 "'
                 ' || kubeadm init --kubernetes-version {kubernetes_version}'
                 ' --service-cidr {service_cidr} --pod-network-cidr {pod_network_cidr}'.format(
                     kubernetes_version=data['kubernetes_version'],
                     service_cidr=data['service_cidr'],
                     pod_network_cidr=data['pod_network_cidr']))

            filer.mkdir('/home/{0}/.kube'.format(env.user))
            sudo('cp /etc/kubernetes/admin.conf /home/{0}/.kube/config'.format(env.user))
            sudo('chown -R {0} /home/{0}/.kube'.format(env.user))
            result = sudo("kubeadm token list | grep 'authentication' | awk '{print $1}'")
            token = str(result)
            databag.set('kubeadm.token', token)

            if data['kubernetes_version'] == 'stable-1.5':
                filer.template('/tmp/calico-1.5.yaml', data=data)
                run('kubectl apply -f /tmp/calico-1.5.yaml')  # noqa
                # run('kubectl apply -f http://docs.projectcalico.org/v2.1/getting-started/kubernetes/installation/hosted/kubeadm/calico.yaml')  # noqa
                # run('kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/master/src/deploy/kubernetes-dashboard-no-rbac.yaml')  # noqa
            if data['kubernetes_version'] == 'stable-1.6':
                filer.template('/tmp/calico-1.6.yaml', data=data)
                print data
                run('kubectl apply -f /tmp/calico-1.6.yaml')  # noqa
                # run('kubectl apply -f http://docs.projectcalico.org/v2.1/getting-started/kubernetes/installation/hosted/kubeadm/1.6/calico.yaml')  # noqa
                # run('kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/master/src/deploy/kubernetes-dashboard.yaml')  # noqa

        else:
            if 'kubeapi_endpoint' in data:
                kubeapi_endpoint = data['kubeapi_endpoint']
            else:
                kubeapi_endpoint = '{0}:6443'.format(
                    env.cluster['node_map']['kubeadm_master']['hosts'][0])

            if 'token' in data:
                token = data['token']
            else:
                token = databag.get('kubeadm.token')
                sudo('ss -ln | grep LISTEN | grep ":4194 " '
                     ' || kubeadm join --token {token} {kubeapi_endpoint}'.format(
                         token=token, kubeapi_endpoint=kubeapi_endpoint))
