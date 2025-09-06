# Containerized Microservice Troubleshooting

## Problem

A new version of a microservice has been deployed to a Kubernetes cluster, but clients report that the service is unreachable. The Kubernetes deployment references a ConfigMap named myapp-config, but
this ConfigMap was never created in the cluster.

## Expected Behavior

The application is expected to load a configuration file from a mounted ConfigMap and
start a web server on port 5000.

## Current Behavior

Pod is stuck in a `CrashLoopBackOff` state, never becomes ready, and requests to the service fail.

### Deployment YAML Snippet

        apiVersion: apps/v1
        kind: Deployment
        metadata:
            name: myapp-deployment
            labels:
                app: myapp
        spec:
            replicas: 1
            template:
                metadata:
                    labels:
                        app: myapp
                spec:
                    containers:
                        - name: myapp-container
                          image: myregistry/myapp:2.0.1
                          ports:
                            - containerPort: 5000
                          env:
                            - name: CONFIG_PATH
                            value: "/etc/myapp/config.yaml"
                          volumeMounts:
                            - name: config-volume
                            mountPath: "/etc/myapp/"  # Mount point for config files
                    volumes:
                        - name: config-volume
                        configMap:
                            name: myapp-config # Reference to ConfigMap (expected to have config.yaml)

### Pod Status

Output of kubectl get pods after deployment:

        NAME                                READY   STATUS              RESTARTS    AGE
        myapp-deployment-5f55c7d6f-abcde    0/1     CrashLoopBackOff    0           3m

Pod Description (Events)
Except from kubectl describe pod myapp-deployment-5f55c7d6f-abcde

        Events:
        Type        Reason      Age     From                    Message
        ----        ------      ----    ----                    -------
        Normal      Scheduled   3m      default-scheduler       Successfully assigned default/myapp-deployment-5f55c7d6f-abcde to node1
        Warning     FailedMount 3m      kubelet                 MountVolume.SetUp failed for volume "config-volume" : configmap "myapp-config" not found
        Warning     FailedMount 2m      kubelet                 Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume
        etc...]: timed out waiting for the condition
        Warning     FailedMount 1m      kubelet                 MountVolume.SetUp failed for volume "config-volume" : configmap "myapp-config" not found

## Root cause Analysis

Error `configmap "myapp-config" not found` in the event log implies that the ConfigMap referenced in the pod spec was not found as named. This could be due to a typo in the name of the ConfigMap, or the ConfigMap doesn't exist in the cluster, or the same namespace as the pod that depends on it. I would confirm that the ConfigMap doesn't exist using the following commands:

1. Check for the ConfigMap in the default namespace:

        kubectl get configmap myapp-config

2. Check for the ConfigMap in all namespaces:

        kubectl get configmap myapp-config --all-namespaces

The results of these commands would detarmine the next steps. For the sake of example, I will assume the scenario is as described and the ConfigMap is not in the cluster at all.

## Proposed solution

### Manual Service Restoration

There is no problem with the way the ConfigMap is referenced in the deployment. First, I would attempt to redeploy the ConfigMap. To do this manually, I would follow these steps:

1. Create a file called `myapp-config.yml` defining the ConfigMap

        apiVersion: v1
        kind: ConfigMap
        metadata:
            name: myapp-config
        data:
            config.yaml: |
                server:
                    port: 5000
                    host: 0.0.0.0
                database:
                    url: postgresql://localhost:5432/myapp
                logging:
                    level: info

1. Create the ConfigMap using kubectl apply -f 

        kubectl apply -f myapp-config.yml

1. Confirm the ConfigMap exists and that it contains the required data:

        # Make sure it's there
        kubectl get configmap myapp-config

        # Check contents
        kubectl describe configmap myapp-config

        # Check raw yaml contents
        kubectl get configmap myapp-config -o yaml

1. Check pod status by label

        kubectl get pods -l app=myapp

1. If pods are still in CrashLoopBackoff, restart the deployment

        kubectl rollout restart deployment myapp-deployment

1. Watch the pods come back up in real-time

        kubectl get pods -l app=myapp -w

1. Check pod events for any remaining issues

        kubectl describe pod -l app=myapp

Assuming the pods came back up without issue, move on to checking service status.

1. Verify the config file is properly mounted

        kubectl exec -it deployment/myapp-deployment -- ls -la /etc/myapp/

        # You should see a config.yaml file here

1. Check the contents of the mounted config file

        kubectl exec -it deployment/myapp-deployment -- cat /etc/myapp/config.yaml

        # The "data" section of the ConfigMap spec should be in this file

1. Check pod logs to ensure application started successfully

        kubectl logs deployment/myapp-deployment

1. Verify the application is listening on port 5000

        kubectl exec -it deployment/myapp-deployment -- netstat -tlnp | grep 5000

At this point, all **looks** like it is in order, so we should confirm the service is available on the expected port

1. If there's a service, check its status

        kubectl get service myapp-service

1. Port-forward to test connectivity

        kubectl port-forward deployment/myapp-deployment 8080:5000 &

1. Test the application endpoint by running curl locally (or navigating to the service in a browser if it has a GUI)

        curl http://localhost:8080/health

1. Stop port-forward

        pkill -f "kubectl port-forward"

Assuming the service is up and available, reach out to users to test and ensure the expected expereience has been restored.

### Next Steps

At this point, service has been restored, but the issue remains that the deployment automation failed. I would work with the team that maintains that automation to ensure the ConfigMap is deployed properly before the pods are deployed.
