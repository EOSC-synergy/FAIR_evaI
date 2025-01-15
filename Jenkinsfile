// SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
// SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
//
// SPDX-License-Identifier: GPL-3.0-only

@Library(['github.com/indigo-dc/jenkins-pipeline-library@2.1.1']) _

def projectConfig

pipeline {
    agent any

    stages {
        stage('SQA baseline criterion: QC.Doc') {
            when {
                anyOf {
                    expression { currentBuild.previousCompletedBuild == null }
                    changeset ".sqa/*"
                    changeset "Jenkinsfile"
                }
            }
            steps {
                script {
                    projectConfig = pipelineConfig(
                        configFile: '.sqa/config.yml',
                        scmConfigs: [ localBranch: true ],
                        validatorDockerImage: 'eoscsynergy/jpl-validator:2.4.0'
                    )
                    buildStages(projectConfig)
                }
            }
            post {
                cleanup {
                    cleanWs()
                }
            }
        }
    }
}