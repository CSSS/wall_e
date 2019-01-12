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
                            "BRANCH=${BRANCH_NAME}",
                            "GUILD_ID=465036366699429888"
                    ]) {
                        String tokenEnv = 'TOKEN'
                        String wolframEnv = 'WOLFRAMAPI'
                        GString testContainerName = "wall-e-test-${BRANCH_NAME}"
                        withCredentials([
                                string(credentialsId: 'TEST_BOT_USER_TOKEN', variable: "${tokenEnv}"),
                                string(credentialsId: 'WOLFRAMAPI', variable: "${wolframEnv}")
                        ]) {
                            sh "docker rm -f ${testContainerName} || true"
                            sh "docker run -d -e ${tokenEnv} -e ${wolframEnv} -e ENVIRONMENT -e BRANCH -e GUILD_ID --net=host --name ${testContainerName} --mount source=${BRANCH_NAME}_logs,target=/usr/src/app/logs wall-e:${env.BUILD_ID}"
                        }
                        sleep 20
                        def containerFailed = sh script: "docker ps -a -f name=${testContainerName} --format \"{{.Status}}\" | grep 'Up'", returnStatus: true
                        if (containerFailed) {
                            def output = sh (
                                    script: "docker logs ${testContainerName}",
                                    returnStdout: true
                            ).trim()
                            withCredentials([string(credentialsId: 'DISCORD_WEBHOOK', variable: 'WEBHOOKURL')]) {
                                discordSend description: BRANCH_NAME + '\n' + output, footer: env.GIT_COMMIT, link: env.BUILD_URL, successful: false, title: 'Failing build', webhookURL: "$WEBHOOKURL"
                            }
                            error output
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
                        String wolframEnv = 'WOLFRAMAPI'
                        String logChannelEnv = 'BOT_LOG_CHANNEL_ID'
                        String productionContainerName = 'wall-e'
                        withCredentials([
                                string(credentialsId: 'BOT_USER_TOKEN', variable: "${tokenEnv}"),
                                string(credentialsId: 'WOLFRAMAPI', variable: "${wolframEnv}"),
                                string(credentialsId: 'BOT_LOG_CHANNEL_ID', variable: "${logChannelEnv}")
                        ]) {
                            sh "docker rm -f ${productionContainerName} || true"
                            sh "docker run -d -e ${tokenEnv} -e ${wolframEnv} -e ${logChannelEnv} -e ENVIRONMENT --net=host --name ${productionContainerName} --mount source=logs,target=/usr/src/app/logs wall-e:${env.BUILD_ID}"
                        }
                    }
                }
            }
        }
    }
    post {
        success {
            withCredentials([string(credentialsId: 'DISCORD_WEBHOOK', variable: 'WEBHOOKURL')]) {
                discordSend description: BRANCH_NAME, footer: env.GIT_COMMIT, link: env.BUILD_URL, successful: true, title: 'Successful build', webhookURL: "$WEBHOOKURL"
            }
        }
    }
}