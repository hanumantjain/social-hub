pipeline {
    agent any

    tools {
        nodejs 'node'
    }

    environment {
        AWS_DEFAULT_REGION = 'us-east-1'
        S3_BUCKET = 'social-frontend-app'
    }
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code'
                git branch: 'main', url: 'https://github.com/hanumantjain/social-hub.git'
            }
        }
        stage('Build Client') {
            steps {
                dir('client') {
                    sh 'npm install'
                    sh 'npm run build'
                }
            }
        }
        stage('Deploy to S3') {     
            steps {
                withAWS(credentials: 'aws-credentials-id', region: "${AWS_DEFAULT_REGION}") {
                    dir('client/dist') {
                        sh '''
                            echo "Listing build output..."
                            ls -lah
                            aws s3 sync . s3://${S3_BUCKET} --delete
                        '''
                    }
                }
            }
        }


        
    }
    post {
        success {
            echo 'Frontend successfully deployed to S3'
        }
        failure {
            echo 'Build or deployment failed'
        }
    }
}