* Git URL
   * Must be same git provider like used otherwise
   * URLs will be parsed org or project and repo name
   * default branch
   * Only  clone once when template.repo == target.repo
* Procedure
   * Read old format in new object structure
   


New
```yaml
apiVersion: v1
applicationName: my-cool-app
previewConfig:
  host: ${PREVIEW_ID}-preview.apps.example.tld
  template:  # optional section
    repository: https://github.com/org/repo.git # would default to `target.repository`
    path: .chart/ # would default to `.preview-templates/${applicationName}`
    branch: master # if not set defaults to feature branch - if template.repository is missing defaults to `target.branch`
  target:
    repository: https://github.com/org/config-repo.git
    branch: main # defaults to repo's default branch (usually master or main)
    namespace: ${PREVIEW_ID}-dev # defaults to `${PREVIEW_ID}-preview` (PREVIEW_ID has max length TBD. Make sure not to exceed 63 chars total)
  replace: 
    values.yaml:
    - path: app.image.tag
      value: ${GIT_COMMIT}
    - path: app.network.http.ingress.host
      value: ${HOST}
    Chart.yaml:
    - path: name
      value: ${PREVIEW_NAMESPACE}
```
Old
```yaml
deploymentConfig:
  # The organisation name of your deployment repo
  org: deployments
  # The repostiory name of your deployment repo
  repository: deployment-config-repo
  # The name of the application (name of the folder in `.preview-templates`)
  applicationName: app-xy

previewConfig:
  route:
    host:
      # Your router host
      # {SHA256_8CHAR_BRANCH_HASH} gets replaced by a shortened hash of your preview_id
      template: app.xy-{SHA256_8CHAR_BRANCH_HASH}.example.tld
  replace:
    # Paths that should be replaced in the `values.yaml`
    - path: image.tag
      variable: GIT_COMMIT # this is the git hash of your app repo
    - path: route.host
      variable: ROUTE_HOST # this is the resolved host.template from above
```

```yaml
apiVersion: v1
applicationName: ".deploymentConfig.applicationName"
previewConfig:
  host: ".previewConfig.route.host.template"
  template:  # optional section
    repository: https://github.com/".deploymentConfig.org"/".deploymentConfig.repository".git # would default to `target.repository`
    path: ".preview-templates/${applicationName}"
    branch: master # if not set defaults to feature branch - if template.repository is missing defaults to `target.branch`
  target:
    repository: https://github.com/".deploymentConfig.org"/".deploymentConfig.repository".git
    branch: main # defaults to repo's default branch (usually master or main)
    namespace: ${PREVIEW_ID}-preview # defaults to `${PREVIEW_ID}-preview` (PREVIEW_ID has max length TBD. Make sure not to exceed 63 chars total)
  replace: 
    values.yaml:
    .previewConfig.replace
```