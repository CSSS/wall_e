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
                    String tokenEnv = 'TOKEN'
                    String testContainerName = 'wall-e-test'
                    withCredentials([string(credentialsId: 'TEST_BOT_USER_TOKEN', variable: "${tokenEnv}")]) {
                        sh "docker rm -f ${testContainerName}"
                        sh "docker run -d -e ${tokenEnv} --net=host --name ${testContainerName} wall-e:${env.BUILD_ID}"
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
                    String tokenEnv = 'TOKEN'
                    String productionContainerName = 'wall-e'
                    withCredentials([string(credentialsId: 'BOT_USER_TOKEN', variable: "${tokenEnv}")]) {
                        sh "docker rm -f ${productionContainerName}"
                        sh "docker run -d -e ${tokenEnv} --net=host --name ${productionContainerName} wall-e:${env.BUILD_ID}"
                    }
                }
            }
        }
    }
}