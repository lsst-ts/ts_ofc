#!/usr/bin/env groovy

pipeline {
    agent any
    stages {
        stage ('Build') {
            steps {
                sh """
                    virtualenv venv
                    . ./venv/bin/activate
                    sudo yum -y update python36
                    sudo yum -y update python36-pip
                    sudo yum -y update python36-devel
                    sudo yum -y update python36-setuptools
                    sudo easy_install-3.6 -U pip
                    pip install -U pip
                """
                sh 'python --version'
                sh 'python3 --version'
                sh 'pip --version'
                sh 'pip3 --version'
            }
        }
        stage ('Install_Requirements') {
            steps {
                sh """
                    pip install numpy scipy pytest
                """
            }
        }
        stage('Unit Tests') {            
            steps {
                sh 'pytest ${WORKSPACE}/tests/*.py'   
            }        
        }
    }
 
    post {        
        always {            
            echo 'One way or another, I have finished'            
            deleteDir() /* clean up our workspace */        
        }        
        success {            
            echo 'I succeeeded!'        
        }        
        unstable {            
            echo 'I am unstable :/'        
        }        
        failure {            
            echo 'I failed :('        
        }        
        changed {            
            echo 'Things were different before...'        
        }    
    }
}
