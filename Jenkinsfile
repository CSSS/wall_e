pipeline {
    agent any
    options {
        disableConcurrentBuilds()
    }
    stages {
        stage('Build') {
            steps {
                script {
                    docker.build("wall-e:${env.BUILD_ID}")
                }
            }
        }
        stage('Test') {
            steps {
                script {
                    withEnv([
                            'ENVIRONMENT=TEST',
                            "BRANCH=${BRANCH_NAME}"
                    ]) {
                        String tokenEnv = 'TOKEN'
                        String logChannelEnv = 'BOT_LOG_CHANNEL_ID'
                        GString testContainerName = "wall-e-test-${BRANCH_NAME}"
                        withCredentials([
                                string(credentialsId: 'TEST_BOT_USER_TOKEN', variable: "${tokenEnv}"),
                                string(credentialsId: 'BOT_LOG_CHANNEL_ID', variable: "${logChannelEnv}")
                        ]) {
                            sh "docker rm -f ${testContainerName} || true"
                            sh "docker run -d -e ${tokenEnv} -e ${logChannelEnv} -e ENVIRONMENT -e BRANCH --net=host --name ${testContainerName} wall-e:${env.BUILD_ID}"
                        }
                    }
                }
            }
        }
        stage('Deploy') {
            when {
                branch 'master'
            }
            steps {
                script {
                    withEnv(['ENVIRONMENT=PRODUCTION']) {
                        String tokenEnv = 'TOKEN'
                        String logChannelEnv = 'BOT_LOG_CHANNEL_ID'
                        String productionContainerName = 'wall-e'
                        withCredentials([
                                string(credentialsId: 'BOT_USER_TOKEN', variable: "${tokenEnv}"),
                                string(credentialsId: 'BOT_LOG_CHANNEL_ID', variable: "${logChannelEnv}")
                        ]) {
                            sh "docker rm -f ${productionContainerName} || true"
                            sh "docker run -d -e ${tokenEnv} -e ${logChannelEnv} -e ENVIRONMENT --net=host --name ${productionContainerName} wall-e:${env.BUILD_ID}"
                        }
                    }
                }
            }
        }
    }
}