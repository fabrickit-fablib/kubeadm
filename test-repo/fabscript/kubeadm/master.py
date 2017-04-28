# coding: utf-8

from fabkit import *  # noqa
from fablib.kubeadm import Kubeadm


@task
def setup():
    kubeadm = Kubeadm(is_master=True)
    kubeadm.setup()
