---
name: helm-generator
description: Create, generate, write or edit Helm templates
---

# Helm Generator

## Overview

This skill provides a comprehensive workflow for generating production-ready helm template according to standards and best practices. 


## When to Use This Skill

Invoke this skill when:
- Creating new Helm charts
- Adding new templates to existing Helm chart 
- Editing existing template in Helm chart 
- Creating new values file
- Updating existing values file 

## Helm Chart Generation Workflow

Follow this workflow when generating Helm charts. Adapt based on user needs:

**Information to Collect:**

   - Which parts of the application are containerized 
   - Is the application stateful / stateless
   - How do you reference application image versioning  
   - Does the application deployment need to follow production standards
   - Port(s) to expose
   - Environment variables needed
   - Health check endpoint (for web services)
   - Volume mounts (if any)

**Plan templates**

Based on the information collected, do the following:

  - Create list of required Kubernetes resources and request approval
  - Create Helm templates of required Kubernetes resources
  - Create example of values.yaml and ask for approval 
  - Create all necessary values.yaml files 

**Use AskUserQuestion if information is missing or unclear.**

**Example Questions:**
```
- Does your application need an ingress to expose its endpoint?
- Which environments needs to run with production high availability standards?
- Does your application need a health check endpoint?
```

