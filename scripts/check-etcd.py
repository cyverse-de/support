#!/usr/bin/env python3

import argparse
import pprint
import subprocess

# Parses the command-line arguments.
def parse_args():
    parser = argparse.ArgumentParser("Check etcd status in a Kubernetes cluster.")
    parser.add_argument(
        "-k", "--kubeconfig", help="The Kubernetes configuration file to use."
    )
    parser.add_argument(
        "-p", "--pod", help="The etcd pod to use when running commands."
    )
    return parser.parse_args()

# Builds the base kubectl command to run for the provided command-line options.
def get_base_kubectl_command(args):
    cmd = ["kubectl", "--namespace=kube-system"]

    # Add the --kubeconfig option if necessary.
    if args.kubeconfig is not None:
        cmd += ["--kubeconfig={0}".format(args.kubeconfig)]

    return cmd

# Determines the default etcd pod to examine. The default is just the first pod in the list for now.
def get_default_etcd_pod(args):
    cmd = get_base_kubectl_command(args) + [
        "get", "pods", "--selector=component=etcd", "--output=jsonpath={.items[0].metadata.name}"
    ]
    proc = subprocess.run(cmd, capture_output=True)
    proc.check_returncode()
    output = proc.stdout.decode()
    if output is None or output == "":
        return None
    return output

# Determines the list of endpoints to use in calls to etcdctl.
def get_endpoint_list(args):
    cmd = get_base_kubectl_command(args) + [
        "get", "pods", "--selector=component=etcd",
        "--output=jsonpath={range .items[*]}https://{.status.podIP}:2379,{end}"
    ]
    proc = subprocess.run(cmd, capture_output=True)
    proc.check_returncode()
    return proc.stdout.decode().rstrip(",")

# Get the endpoint status.
def get_etcd_endpoint_status(args, pod, endpoints):
    cmd = get_base_kubectl_command(args) + [
        "exec", pod, "--", "etcdctl", "--endpoints={0}".format(endpoints),
        "--cacert=/etc/kubernetes/pki/etcd/ca.crt",
        "--key=/etc/kubernetes/pki/etcd/server.key",
        "--cert=/etc/kubernetes/pki/etcd/server.crt",
        "--write-out=table",
        "endpoint", "status"
    ]
    proc = subprocess.run(cmd)
    proc.check_returncode()

if __name__ == "__main__":
    args = parse_args()

    # Determine which pod to use when calling etcd.
    pod = args.pod
    if pod is None:
        pod = get_default_etcd_pod(args)

    # Get the list of endpoints to use in etcdctl calls.
    endpoints = get_endpoint_list(args)

    # List the etcd cluster members.
    get_etcd_endpoint_status(args, pod, endpoints)
