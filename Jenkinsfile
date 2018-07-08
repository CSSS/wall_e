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
                        sh "docker stop ${testContainerName} || true"
                        sh "docker rm ${testContainerName} || true"
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
                        sh "docker stop ${productionContainerName} || true"
                        sh "docker rm ${productionContainerName} || true"
                        sh "docker run -d -e ${tokenEnv} --name ${productionContainerName} wall-e:${env.BUILD_ID}"
                    }
                }
            }
        }
    }
}