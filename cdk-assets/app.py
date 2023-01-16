from stacks.glue_pipeline_stack import *

app = cdk.App()
GluePipelineStack(app, "GluePipelineStack")
cdk.Tags.of(app).add('creator', 'anna-pastushko')
cdk.Tags.of(app).add('owner', 'ml-team')
app.synth()
