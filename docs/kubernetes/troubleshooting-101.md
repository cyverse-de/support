# Troubleshootng 101

This document discusses some problems that sometimes arise along with some common troubleshooting steps. This is not
meant to be an exhaustive resource, but it can serve as a useful starting point.

## Useful Tools

### kubectl

Kubectl is the command line interface for Kubernetes, and it's the most common way to get information about
Kubernetes.

### kubetail

When you're trying to simultaneously follow logs for a replicated service, `kubectl logs` doesn's quite satisfy the
need. It becomes necessary to keep multiple terminals open and to collate the log messages manually in order to
determine what's going on. [kubetail][1] fills this niche quite nicely.

## Etcd

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
namespace. The easiest way to do this is to use `kubetail`:

```
$ kubetail -n kube-system logs -l component=etcd
```

The `etcd` pod names follow a specific pattern: `etcd-<node-name>`, where `<node-name>` is the name of the Kubernetes
controller node that the pod happens to be running on. For example, if we have a controller node named
`controller-1.example.org`, the name of the `etcd` pod running on that node would be
`etcd-controller-1.example.org`. With this information in hand, you can also monitor the `etcd` logs on a specific node
using `kubectl logs`, for example:

```
$ kubectl logs -n kube-system etcd-controller-1.example.org
```

When the leader is being changed repetitively, you'll typically see messages such as this:

```
etcdserver: failed to send out heartbeat on time (exceeded the 100ms timeout for 53.225738ms, to fdb42e1bf60a1303)
```

These messages will also appear when `etcd` is overloaded, so these message aren't uncommon, even when there are no
network issues. Troubleshooting issues with the overlay network is a separate topic covered elsewhere in this document.

### Checking Etcd Cluster Health

This task is fairly common, so we created a [script][../../scripts/check-etcd.py] to make this process a little
easier. To use this script, you'll need to know the name of one of the `etcd` pods, which can be determined using the
naming convention described above. If one of the etcd pods is `etcd-controller-1.example.org`, you can display some
information about the cluster by running this command:

```
$ ./scripts/check-etcd.py -p etcd-controller-1.example.org
+----------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
|          ENDPOINT          |        ID        | VERSION | DB SIZE | IS LEADER | IS LEARNER | RAFT TERM | RAFT INDEX | RAFT APPLIED INDEX | ERRORS |
+----------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
| https://10.140.65.163:2379 | 661494d083bf191b |  3.4.13 |  112 MB |     false |      false |      2024 |  257730105 |          257730105 |        |
| https://10.140.65.164:2379 | 98276553b46311bf |  3.4.13 |  111 MB |      true |      false |      2024 |  257730105 |          257730105 |        |
| https://10.140.65.165:2379 | cb2ed03196903678 |  3.4.13 |  111 MB |     false |      false |      2024 |  257730105 |          257730105 |        |
| https://10.140.65.176:2379 | fdb42e1bf60a1303 |  3.4.13 |  112 MB |     false |      false |      2024 |  257730105 |          257730105 |        |
| https://10.140.65.177:2379 | 6d09ac4a745ac3e6 |  3.4.13 |  112 MB |     false |      false |      2024 |  257730105 |          257730105 |        |
+----------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
```

If you want to use something other than the default Kubernetes configuration file, you can use the `--kubeconfig` or
`-k` command-line option, for example:

```
$ ./scripts/check-etcd.py -p etcd-controller-1.example.org -k ~/.kube/config.prod
+----------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
|          ENDPOINT          |        ID        | VERSION | DB SIZE | IS LEADER | IS LEARNER | RAFT TERM | RAFT INDEX | RAFT APPLIED INDEX | ERRORS |
+----------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
| https://10.140.65.163:2379 | 661494d083bf191b |  3.4.13 |  112 MB |     false |      false |      2024 |  257730105 |          257730105 |        |
| https://10.140.65.164:2379 | 98276553b46311bf |  3.4.13 |  111 MB |      true |      false |      2024 |  257730105 |          257730105 |        |
| https://10.140.65.165:2379 | cb2ed03196903678 |  3.4.13 |  111 MB |     false |      false |      2024 |  257730105 |          257730105 |        |
| https://10.140.65.176:2379 | fdb42e1bf60a1303 |  3.4.13 |  112 MB |     false |      false |      2024 |  257730105 |          257730105 |        |
| https://10.140.65.177:2379 | 6d09ac4a745ac3e6 |  3.4.13 |  112 MB |     false |      false |      2024 |  257730105 |          257730105 |        |
+----------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
```

In this example, the cluster is healthy. Any errors that are currently affecting one of the `etcd` nodes will appear in
the `ERRORS` column. In the event of an error, please see the [etcd documentation][2].

## Overlay Network

Kubernetes uses an overlay network to simplify communication between pods. This abstraction means that services running
inside Kubernetes can find each other without having to know anything about the network topology outside the
cluster. This allows us to easily add replicas of services in a fault-tolerant way without having to add complexity to
our services. This abstraction layer does add an additional layer of complexity to the overlay network itself,
however. When network connection issues occur, it's sometimes necessary to troubleshoot the overlay network.

### Examining Logs

Our Kubernetes clusters use `weave-net` for the overlay network, and the network pods run in the `kube-system`
namespace. The easiest way to examine the logs, as you might expect, is to use `kubetail`:

```
$ kubetail -n kube-system -l name=weave-net
```

The amount of information that this command produces quickly becomes overwhelming. You can limit the output by
specifying the name of the container. The options for the container name are `weave` and `weave-npc`. There's also an
initialization container called `weave-init`, but examining its logs is unhelpful unless you're troubleshooting a
recently added Kubernetes node. You can tell `kubetail` to limit the logs to speicfic container names using the
`--container` or `-c` command-line argument, for example:

```
$ kubetail -n kube-system -l name=weave-net -c weave
```

If you want to examine the logs on a specific node, you'll need to find the name of the pod first. The easiest way to
get the name of a `weave-net` pod running on a specific host is to use `kubectl get pods` with a combination of the
`--selector` (or `-l` for short) and `--field-selector` command-line options:

```
$ kubectl get pods -n kube-system -l name=weave-net --field-selector spec.nodeName=<node-name>
```

In this example, `<node-name>` is the name of the node for which you want to examine logs. For example:

```
$ kubectl get pods -n kube-system -l name=weave-net --field-selector spec.nodeName=worker-1.example.org
NAME              READY   STATUS    RESTARTS   AGE
weave-net-hpz7p   2/2     Running   0          6d5h
```

With this information in hand, you can use `kubectl logs` to look at the log messages, for example:

```
$ kubectl logs -n kube-system weave-net-hpz7p weave
```

Note that this command specifies the name of the container. If you don't specify the container name, `kubectl logs` will
choose a default container for you. This can be confusing if the default container name doesn't happen to be the one you
want to examine.

### Forcing a Restart

Assuming that the physical network is working correctly and the overlay network is still misbehaving, it's frequently
sufficient to simply restart the `weave-net` pods. If the entire clsuter seems to be misbehaving, you can simply force a
restart of all weave-net pods in the cluster:

```
$ kubectl rollout -n kube-system restart daemonset/weave-net
daemonset.apps/weave-net restarted
```

If the network seems to be misbehaving on a specific node, you can force a restart on just that node by deleting the
existing pod:

```
$ kubectl delete pods -n kube-system -l name=weave-net --field-selector spec.nodeName=worker-1.example.org
pod "weave-net-5bgjh" deleted
```

In the rare case that restarting the pod doesn't work, it sometimes help to drain the node and reboot it:

```
$ kubectl drain worker-1.example.org --ignore-daemonsets --delete-emptydir-data
```

Once the node has successfully been drained, you can reboot it as usual.

[1]: https://github.com/johanhaleby/kubetail
[2]: https://etcd.io/docs/v3.4/
