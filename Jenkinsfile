pipeline {
    agent any
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
                        sh "docker stop ${testContainerName}"
                        sh "docker rm ${testContainerName}"
                        sh "docker run -d -e ${tokenEnv} --name ${testContainerName} wall-e:${env.BUILD_ID}"
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
                        sh "docker stop ${productionContainerName}"
                        sh "docker rm ${productionContainerName}"
                        sh "docker run -d -e ${tokenEnv} --name ${productionContainerName} wall-e:${env.BUILD_ID}"
                    }
                }
            }
        }
    }
}