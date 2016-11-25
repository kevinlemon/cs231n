import numpy as np  
from multiprocessing  import Pool
# iSigma={}
import scipy
from sklearn.externals import joblib
from scipy.linalg import get_blas_funcs
# gemm = get_blas_funcs("gemm", [X, Y])
def gauss(X,U,Sigma):
    
    r=scipy.stats.multivariate_normal.pdf(x=X,mean=U,cov=Sigma)
    
    return r
    
def rel_error(x, y):
  """ returns relative error """
  return np.max(np.abs(x - y) / (np.maximum(1e2, np.abs(x) + np.abs(y))))
 
def gauss_p(x):
    return gauss(x[0],x[1],x[2])
 
def h_function(x):
#     print 'ww'
    print time.time(),'-1---'
    tt=np.linalg.inv( x[1])
    print time.time(),'-2---'
    tmp1=x[0].dot( tt)
    # tmp1 = get_blas_funcs("gemm", [x[0], tt])
    print time.time(),'-3---'
    tmp=np.trace(tmp1,axis1=2,axis2=3)
    print time.time(),'-4---'
    r=np.exp(-0.5*tmp)
    print time.time(),'-5---'
    return r
import time

class EM_extended:
     
    def __init__(self,U,Sigma,Pi,M=64,max_iteration=1,toi=1e-2,verbose=1):
        self.K,self.D,self.feature_size=U.shape
        self.M=M
        self.U=np.random.random([M,self.feature_size])*0.0001+np.mean(U,axis=0).mean(axis=0)### M*192
        self.Sigma=np.eye(self.feature_size)+np.zeros([M,self.feature_size,self.feature_size])#M*192*192
        # # print self.Sigma,np.linalg.inv(self.Sigma)
        # print self.Sigma.shape
        self.Pi=np.ones(M)/M #M
        self.iU=U#K*D*192
        self.iSigma=Sigma#K*D*192*192
        self.iPi=Pi#K*D
        self.max_iteration=max_iteration
        self.toi=toi
        self.verbose=verbose
        self.h=np.zeros([self.K,self.D,self.M])##K,D,M
        
      
    def train(self):
        M,K,D=self.M,self.K,self.D
        p=Pool(16)
        pre_param=(self.U,self.Sigma,self.Pi)

        ii=0
        error=self.toi+1
        while(ii<self.max_iteration and error>self.toi ):
            print 'error', error
            if( self.verbose>0):
                if ii%self.verbose==0:print "iteration %s" %ii
            ii+=1

            # E STEP
            print time.time(),'a'
            gauss_var=(zip([self.iU.reshape(K*D,self.feature_size)]*self.U.shape[0],\
                                          self.U,self.Sigma))
            result=p.map(gauss_p,gauss_var) #M,K,D  #compute gauss 
            print time.time(),'b'
            h_g=np.transpose(np.array(result).reshape(M,K,D),[1,2,0])\
                .reshape(K,D,M)#K,D,M
            print time.time(),'c'
#             h_function=lambda x:np.exp(-0.5*\
#                 np.trace(self.iSigma.dot(np.linalg.inv( x) ),axis1=2,axis2=3))
#             print 'sdg'

            # compute next one
            print time.time(),'d'
            result=p.map(h_function,list(zip([self.iSigma]*self.Sigma.shape[0],self.Sigma))) #M,K*D
            print time.time(),'e'
            h_e=np.transpose(np.array(result),[1,2,0])
            fenmu=np.power(h_g*h_e,self.iPi.reshape(K,D,1))*(self.Pi)
            print time.time(),'f'
            fm= (np.sum(fenmu,axis=2).reshape(K,D,1))
            print time.time(),'g'
            eps=1e-6
            self.h=(fenmu+eps/M)/(fm+eps)
            print time.time(),'h'
            print 'sss',self.h[self.h>1/64.0]
 
            # M STEP
            self.Pi=self.h.sum(axis=0).sum(axis=0)/(D*K)
            w=self.h*(self.iPi.reshape(K,D,1))
            print time.time(),'ggg'
            w/=(w.sum(axis=0).sum(axis=0))
            print time.time(),'gg2'
            self.U=(w.reshape(K,D,M,1)*(self.iU.reshape(K,D,1,self.feature_size)))\
                .sum(axis=0).sum(axis=0)
            print time.time(),'g3'
            iSigma_t=self.iSigma.reshape(K,D,1,self.feature_size,self.feature_size)
            print time.time(),'g3-'
            sigma_iu=self.iU.reshape(K,D,1,self.feature_size,1)
            print time.time(),'g3-'
            sigma_u=self.U.reshape(1,1,M,self.feature_size,1)
            print time.time(),'g3-'
            u_delta=sigma_iu-sigma_u
            print time.time(),'g3-'
            u_delta2=u_delta.reshape(K,D,M,1,self.feature_size)
            print time.time(),'g3-'
            sigma_w=w.reshape(K,D,M,1,1)
            print time.time(),'g3-'
            sigma_tmp=sigma_w*(iSigma_t+(u_delta)*(u_delta2))#K D M feature feature
            print time.time(),'g4'
            print sigma_tmp.shape
            self.Sigma=sigma_tmp.sum(axis=0).sum(axis=0)

            error1=rel_error(self.U,pre_param[0])
            error2=rel_error(self.Sigma,pre_param[1])
            # np.max(np.abs(self.U-pre_param[0]))/np.max(np.abs(self.U))
            # error2=np.max(np.abs(self.Sigma-pre_param[1]))/np.max(np.abs(self.Sigma))
            # # error3=np.max(np.abs(self.Pi-pre_param[2]))
            error=max(error1,error2)
             
        p.terminate()
        if ii==self.max_iteration:
            print 'warning: not converge'
        else:
            print 'converge'
        return self
    def score(self,X):
        for ii in range(self.M):
            results=map(lambda (u,cov,pi):pi*gauss(X,u,cov),zip(self.U,self.Sigma,self.U))
        return np.sum(results)

def load_data():
    all_data=np.load('dct_feature.npz')
    # data=all_data['data']
    # labels=all_data['labels']
    # label_str=all_data['label_str']
    return all_data


from sklearn.mixture import GaussianMixture


class Solver:
    def __init__(self,class_label):
        weights,means,cov=[],[],[]
        class_labels_images=np.arange(5000)[load_data()['labels'][:,class_label]>0]
        print class_labels_images
         
        for ii in class_labels_images:
            model=joblib.load('/home/x/data/gmm_model/gmm/model%s' %ii)
            weights.append(model.weights_)
            means.append(model.means_)
            cov.append(model.covariances_)
        Pi=np.array(weights)
        U=np.array(means)
        Sigma=np.array(cov)
        print U.shape ,Pi.shape ,Sigma.shape 
        U=np.transpose(U,[1,0,2])
        Sigma=np.transpose(Sigma,[1,0,2,3])
        m=EM_extended(U,Sigma,Pi)
        self.m=m.train()
        
    
    def test(self,image):
        m=Gauss
        result =0
        for ybr in image:
            result+=(np.log(self.m.score(ybr)))
        return result
    def test_all(self,data):
        '''

        '''
        print 'hh;'
        N,H,W,Chanel,windows1,windows2=data.shape
        images=data.reshape(N,H*W,Chanel*windows1*windows2)
        p=Pool(16)
        scores=p.map(lambda x:self.test(x),images)
        p.terminate()
        return scores
