#!/bin/bash

# Generate minimal IAM policy for Cluster Autoscaler

CLUSTER_NAME="${1:-my-cluster}"

cat << POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeAutoScalingInstances",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeScalingActivities",
        "autoscaling:DescribeTags",
        "ec2:DescribeImages",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:GetInstanceTypesFromInstanceRequirements",
        "eks:DescribeNodegroup"
      ],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:SetDesiredCapacity",
        "autoscaling:TerminateInstanceInAutoScalingGroup"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "autoscaling:ResourceTag/k8s.io/cluster-autoscaler/${CLUSTER_NAME}": "owned"
        }
      }
    }
  ]
}
POLICY

echo -e "\nTo create IAM policy:"
echo "aws iam create-policy --policy-name ClusterAutoscalerPolicy --policy-document file://policy.json"
echo ""
echo "To attach to role:"
echo "aws iam attach-role-policy --role-name <autoscaler-role> --policy-arn <policy-arn>"
