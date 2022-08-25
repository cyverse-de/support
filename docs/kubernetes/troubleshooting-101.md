# Troubleshootng 101

This document discusses some problems that sometimes arise along with some common troubleshooting steps. This is not
meant to be an exhaustive resource, but it can serve as a useful starting point.

## Useful Tools

### kubectl

Kubectl is the command line interface for Kubernetes, and it's the most common way to get information about Kubernetes.

## Etcd Error Messages

Our Kubernetes clusters use etcd to store information about all of the resources that are currently defined in the
cluster, which makes etcd absolutely critical to the operation of the cluster. Problems with etcd are uncommon, but
because etcd is so crucial to the operation of the cluster, they are frequently severe when they do occur.

### Error: Unable to Elect a Leader

We've only encountered this error message twice: once in each cluster. Unfortunately, we've been unable to recover from
this error message both times it occurred. The only solution that we've found is to tear down the cluster and build it
back up again. Please contact the DE team if you encounter this message.

### Error: Etcd Leader Changed

The etcd cluster normally won't elect a new leader unless it detects a potential problem, but it does happen relatively
frequently. In most cases, the problem resolves itself after a few minutes. In rarer cases, the problem may last a few
hours, however, and this will cause an extended service outage in the Discovery Environment. We've seen two common
causes of this in our Kubernetes clusters at CyVerse.

The first cause is routine system mainteance. During maintenance days, we install system updates on our Kubernetes
nodes. We must reboot the control nodes when they're being updated, which will cause the etcd leader to become available
at least once. In this case, the error messages are expected, and the problem usually resolves itself once the
maintenance is complete.

The second common cause is network connectivity issues. Normally, we'd expect this to be rare because all of the control
nodes are on the same subnet in both of our Kubernetes clusters. It does happen fairly frequently, however. Because the
etcd instances are running inside Kubernetes, multiple network layers are involved. When this does happen, the easiest
place to look for trouble is in the etcd logs. You can view the logs by examining the etcd pods in the `kube-system`
namespace.
