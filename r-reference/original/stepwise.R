rm(list=ls())

load("dati_info.RData")
dati.info=dati
load("datiScale_w1w2.RData")
dati.testAtt=dati
load("dati_mess_wall_parole.RData")

#controllo che variabili ci sono
names(dati.info)
names(dati)
names(dati.testAtt)

#tolgo la riga ripetuta su dati.info
dim(dati.info)[1]
length(unique(dati.info$CODICE.ZIP)) 
table(dati.info$CODICE.ZIP)[table(dati.info$CODICE.ZIP)>1]
dati.info[dati.info$CODICE.ZIP=="CODICE_REDATTO",]
dati.info=dati.info[-301,]
dim(dati.info)[1]
length(unique(dati.info$CODICE.ZIP))

#tolgo la riga ripetuta su dati
dim(dati)[1]
length(unique(dati$CODICE.ZIP)) 
table(dati$CODICE.ZIP)[table(dati$CODICE.ZIP)>1]
dati[dati$CODICE.ZIP=="CODICE_REDATTO",1:5]
dati=dati[-283,]
dim(dati)[1]
length(unique(dati$CODICE.ZIP))

#creo dataset unico per usare la funzione step

#dati: informazione attività facebook (righe 324)
#dati.info: info generali sul soggetto (righe 345)
#dati.testAtt: test attitudinali (righe 1420)

#somma colonne: 530+9+63

pos=match(dati$CODICE.ZIP, dati.info$CODICE.ZIP)
merge.dati=data.frame(dati,dati.info[pos,])

pos=match(merge.dati$CODICE.ZIP, dati.testAtt$CODICE.ZIP)
merge.dati=data.frame(merge.dati,dati.testAtt[pos,])

dim(merge.dati)

str(merge.dati$sesso)
merge.dati$sesso=as.factor(merge.dati$sesso)
contrasts(merge.dati$sesso)
str(merge.dati$sesso)

merge.dati$CODICE.ZIP=NULL  #elimina la colonna (se si fa dim(merge.dati) c'è una colonna in meno)
merge.dati$CODICE.ZIP.1=NULL 
merge.dati$CODICE.ZIP.2=NULL 
merge.dati$msg_MFprops.maschi=NULL 

pos=rep(NA,598)
for(i in 1:598){
  pos[i]=is.character(merge.dati[,i])
}
table(pos)
str(merge.dati[,pos])

merge.dati$nome=as.factor(merge.dati$nome)
str(merge.dati$nome)
merge.dati$email=as.factor(merge.dati$email)
str(merge.dati$email)
merge.dati$cittaNatale=as.factor(merge.dati$cittaNatale)
str(merge.dati$cittaNatale)
merge.dati$situazSentim=as.factor(merge.dati$situazSentim)
str(merge.dati$situazSentim)

#cerco la variabile sesso
for(i in 1:598){
  if(names(merge.dati)[i]=="sesso") j=i
}
j  #sesso è la variabile 533
X=merge.dati[,-j]   #matrice delle esplicative

dim(merge.dati)
dim(X)
#ho 324 osservazioni: 70 per l'insieme di test e 324-70 per l'insieme di allenamento del modello
set.seed(50)   
idx=sample(1:nrow(merge.dati), 70)  
idx
length(idx)
length(unique(idx))
X.train=X[-idx,]
dim(X.train)
y.train=merge.dati$sesso[-idx]
length(y.train)
X.test=X[idx,]
dim(X.test)
y.test=merge.dati$sesso[idx]
length(y.test)
#254+70=324

#colonne buone:  (numeriche)
str(X.train[,1:50])
str(X.train[,51:100])
str(X.train[,101:150])
str(X.train[,151:200])
str(X.train[,201:250])
str(X.train[,251:300])
str(X.train[,301:350])
str(X.train[,351:400])
str(X.train[,401:450])
str(X.train[,451:500])
str(X.train[,c(501:528,536:550)])
str(X.train[,c(551:568,593:597)])

#colonne da togliere: (non numeriche)
str(X.train[,c(529:535,569:592)])

X.train=X.train[,-c(529:535,569:592)]
X.test=X.test[,-c(529:535,569:592)]

#############################################################################
#############################################################################

# <redacted>

#write.table(cbind(y.train,X.train),"training.dat",row.names=F)
#write.table(cbind(y.test,X.test),"test.dat",row.names=F)

#train=read.csv2("training.csv")

#############################################################################
#############################################################################

x=model.matrix(~.,data=X.train)
dim(x)
#colnames(x)

dim(X.train)
pos=rep(NA,566)
for(i in 1:566){
  pos[i]=is.numeric(X.train[,i])
}
table(pos)
str(X.train[,!pos])  #sono le variabili non numeriche presenti nel dataset
                     #hanno tutte tanti livelli, le tolgo dal dataset
X1.train=X.train[,pos]
dim(X1.train)

pos=rep(NA,566)
for(i in 1:566){
  pos[i]=length(unique(X1.train[,i]))==1  #sono le variabili che assumono valore costante in tutte le unità
}
table(pos)  #sono 31
str(X1.train[,pos])   #sono parole che nessuno di questi 254 soggetti ha mai utilizzato
X1.train=X1.train[,!pos]
dim(X1.train)

x1=model.matrix(~.,data=X1.train)
str(x1)
colnames(x1)

formula_completa <- as.formula(paste("y.train ~", paste(colnames(x1)[-1], collapse = "+")))
formula_completa

dim(X1.train)
table(apply(X1.train,1,function(x) all(is.na(x))))

fit0=glm(y.train~1,family=binomial)
length(fitted(fit0))
summary(fit0)

attach(X1.train)
step(fit0,direction="both",scope=formula_completa)  

#NO
fit=glm(y.train ~ msg_MFprops.femmine + msg_freq_ore.04 + others_personal.oppresso + 
          others_grp.conto + wall_freq_ore.00 ,binomial,na.action = "na.exclude")

#matrice_fit=cbind(msg_MFprops.femmine, msg_freq_ore.04, others_personal.oppresso, 
#                    others_grp.conto , wall_freq_ore.00)
#dim(matrice_fit)
#table(apply(matrice_fit,1,function(x) all(is.na(x))))

summary(fit)
length(fitted(fit))
hist(fitted(fit))
#(per confronto)
table(as.numeric(y.train=="M"),fitted(fit)>0.5)
sum(diag(table(as.numeric(y.train=="M"),fitted(fit)>0.5)))/
  sum(table(as.numeric(y.train=="M"),fitted(fit)>0.5))
#sull'insieme di test
table(as.numeric(y.test=="M"),plogis(predict(fit,newdata=X.test))>0.5)
sum(diag(table(as.numeric(y.test=="M"),plogis(predict(fit,newdata=X.test))>0.5)))/
  sum(table(as.numeric(y.test=="M"),plogis(predict(fit,newdata=X.test))>0.5))


#fit_lasso=glm(formula = y.train ~ msg_MFprops.femmine + msg_freq_ore.04 + 
#                others_personal.oppresso + others_grp.conto + wall_freq_ore.00, 
#              family = binomial)
#summary(fit)
#hist(fitted(fit))
#table(fitted(fit)==1)
#dim(matrice_modello)
#table(apply(matrice_modello,1,function(x) all(is.na(x))))

step(fit,direction="both",scope=formula_completa, na.action = "na.exclude") 

fit_step2=glm(formula = y.train ~ msg_MFprops.femmine + msg_freq_ore.04 + 
                others_personal.oppresso + others_grp.conto + wall_freq_ore.00 + 
                wall_freq_giorni.domenic + wall_azioni.w_nuovaFoto + others_grp.senti + 
                user_personal.incubo, family = binomial, na.action = "na.exclude")

summary(fit_step2)
hist(fitted(fit_step2))
#su train
table(as.numeric(y.train=="M"),fitted(fit_step2)>0.5)
sum(diag(table(as.numeric(y.train=="M"),fitted(fit_step2)>0.5)))/
  sum(table(as.numeric(y.train=="M"),fitted(fit_step2)>0.5))
library(pROC)
plot(roc(as.numeric(y.train=="M"),fitted(fit_step2)),legacy.axes=T,print.auc=T,asp=F)
AIC(fit_step2)

#su test
table(as.numeric(y.test=="M"),plogis(predict(fit_step2,newdata=X.test))>0.5)
sum(diag(table(as.numeric(y.test=="M"),plogis(predict(fit_step2,newdata=X.test))>0.5)))/
  sum(table(as.numeric(y.test=="M"),plogis(predict(fit_step2,newdata=X.test))>0.5))
plot(roc(as.numeric(y.test=="M"),plogis(predict(fit_step2,newdata=X.test))),legacy.axes=T,print.auc=T,asp=F)

############

#provo a cambiare la soglia e valutare l'accuratezza
acc_soglia=NULL
sequenza=seq(0.4,0.43,by=0.001)
for(soglia in sequenza){
  acc_soglia=c(acc_soglia,sum(diag(table(as.numeric(y.test=="M"),plogis(predict(fit_step2,newdata=X.test))>soglia)))/sum(table(as.numeric(y.test=="M"),plogis(predict(fit_step2,newdata=X.test))>soglia)))
}
cbind(sequenza,acc_soglia)
plot(sequenza,acc_soglia,type="l")

#scelgo soglia 0.42
table(as.numeric(y.test=="M"),plogis(predict(fit_step2,newdata=X.test))>0.42)
sum(diag(table(as.numeric(y.test=="M"),plogis(predict(fit_step2,newdata=X.test))>0.42)))/
  sum(table(as.numeric(y.test=="M"),plogis(predict(fit_step2,newdata=X.test))>0.42))

############
#tolgo var non signif da fit_step2
summary(fit_step2)

fit_step22=glm(formula = y.train ~ msg_MFprops.femmine + msg_freq_ore.04 + 
                others_personal.oppresso + others_grp.conto + wall_freq_ore.00 + 
                wall_freq_giorni.domenic + wall_azioni.w_nuovaFoto + others_grp.senti, 
               family = binomial, na.action = "na.exclude")
summary(fit_step22)
#su test
table(as.numeric(y.test=="M"),plogis(predict(fit_step22,newdata=X.test))>0.5)
sum(diag(table(as.numeric(y.test=="M"),plogis(predict(fit_step22,newdata=X.test))>0.5)))/
  sum(table(as.numeric(y.test=="M"),plogis(predict(fit_step22,newdata=X.test))>0.5))
plot(roc(as.numeric(y.test=="M"),plogis(predict(fit_step22,newdata=X.test))),legacy.axes=T,print.auc=T,asp=F)
AIC(fit_step22)
#non migliora di molto...

#############
step(fit_step2,direction="both",scope=formula_completa, na.action = "na.exclude") 

fit_step3=glm(formula = y.train ~ msg_MFprops.femmine + msg_freq_ore.04 + 
                others_personal.oppresso + others_grp.conto + wall_freq_ore.00 + 
                wall_freq_giorni.domenic + wall_azioni.w_nuovaFoto + others_grp.senti + 
                user_personal.incubo + others_grp.EMOTELOVE + others_grp.cazzata + 
                user_personal.cazzata + others_grp.EMOTEOHOH + wall_freq_ore.09 + 
                msg_freq_ore.05, family = binomial, na.action = "na.exclude")

summary(fit_step3)
hist(fitted(fit_step3))
#su train
table(as.numeric(y.train=="M"),fitted(fit_step3)>0.5)
sum(diag(table(as.numeric(y.train=="M"),fitted(fit_step3)>0.5)))/
  sum(table(as.numeric(y.train=="M"),fitted(fit_step3)>0.5))
plot(roc(as.numeric(y.train=="M"),fitted(fit_step3)),legacy.axes=T,print.auc=T,asp=F)
AIC(fit_step3)

#su test
table(as.numeric(y.test=="M"),plogis(predict(fit_step3,newdata=X.test))>0.5)
sum(diag(table(as.numeric(y.test=="M"),plogis(predict(fit_step3,newdata=X.test))>0.5)))/
  sum(table(as.numeric(y.test=="M"),plogis(predict(fit_step3,newdata=X.test))>0.5))
plot(roc(as.numeric(y.test=="M"),plogis(predict(fit_step3,newdata=X.test))),legacy.axes=T,print.auc=T,asp=F)

#######################

#                               fit_step2        fit_step3
#accuratezza su test               0.76            0.79 *
#AUC su test                       0.65 *          0.57
#AIC su train                      169             162 *
#BIC su train                      203 *           217
#n variabili non signif            2 *             10

########################
step(fit_step3,direction="both",scope=formula_completa, na.action = "na.exclude") 

#NO
fit_step4=glm(formula = y.train ~ msg_MFprops.femmine + msg_freq_ore.04 + 
                others_personal.oppresso + others_grp.conto + wall_freq_ore.00 + 
                wall_freq_giorni.domenic + wall_azioni.w_nuovaFoto + others_grp.senti + 
                user_personal.incubo + others_grp.EMOTELOVE + others_grp.cazzata + 
                user_personal.cazzata + others_grp.EMOTEOHOH + wall_freq_ore.09 + 
                msg_freq_giorni.mercoled + msg_freq_ore.05, family = binomial, 
              na.action = "na.exclude")
summary(fit_step4)
#su test
table(as.numeric(y.train=="M"),fitted(fit_step4)>0.5)
sum(diag(table(as.numeric(y.train=="M"),fitted(fit_step4)>0.5)))/
  sum(table(as.numeric(y.train=="M"),fitted(fit_step4)>0.5))
#su test
table(as.numeric(y.test=="M"),plogis(predict(fit_step4,newdata=X.test))>0.5)
sum(diag(table(as.numeric(y.test=="M"),plogis(predict(fit_step4,newdata=X.test))>0.5)))/
  sum(table(as.numeric(y.test=="M"),plogis(predict(fit_step4,newdata=X.test))>0.5))






################################################
str(y.train)  #ha 2 livelli
colnames(x1)[1:2]
str(msg_n_user)  #è numerica

flag=rep(NA,dim(X1.train)[2])
for(i in 1:dim(X1.train)[2]){
  flag[i]=all(is.na(X1.train[,i]))  #controllo se ci sono colonne con tutti valori NA
}
table(flag)  #non ci sono

#provo a usare la funzione leaps() per la regressione stepwise
library(leaps)
#?leaps

# COME POSSO SPECIFICARE DI ADATTARE UN MODELLO BINOMIALE?
m1=leaps(x, y.train, int = FALSE)  # DA ERRORE (più di 31 variabili)

#ho tanti regressori, uso regsubsets()
#?regsubsets
#str(X.train)
#model=regsubsets(as.matrix(X1.train),y.train)   # NON VA

#provo a farne le componenti principali per ridurre la dimensionalità
#?princomp
#pc=princomp(x1[,-1])  #non si può fare se n < p

str(X1.train)
X1.train=as.matrix(X1.train)  

inv=scale(X1.train)
dim(inv)

flag=rep(NA,dim(inv)[2])
for(i in 1:dim(inv)[2]){
  flag[i]=all(is.na(inv[,i])) 
}
table(flag) #nella matrice inversa ci sono 8 colonne nulle, quindi nella matrice 
            #X1.train ci sono 8 colonne di soli zeri/NA?
str(as.data.frame(X1.train)[,flag])
dim(X1.train)
X1.train=X1.train[,!flag]
dim(X1.train)
#549-8=541

x1=model.matrix(~.,data=X1.train)
str(x1)
colnames(x1)

formula_completa <- as.formula(paste("y.train ~", paste(colnames(x1)[-1], collapse = "+")))
formula_completa

detach()
attach(X1.train)
step(fit0,direction="both",scope=formula_completa)

# LA COLONNA AIC NON RIPORTA L'AIC DEL MODELLO CON QUELLA VARIABILE AGGIUNTA.
# INFATTI SE SI AGGIUNGE msg_MFprops.femmine (UNDICESIMA VARIABILE NELL'ELENCO
# DELL'OUTPUT DELLA FUNZIONE step()) L'AIC E' DI 228.59 (INFERIORE A QUELLO DEL 
# MODELLO NULLO DI 248.25) E NON DI  250.25 COME RIPORTATO NELL'OUTPUT
# DELLA FUNZIONE step()

X1.train$msg_MFprops.femmine
fit1=glm(y.train~msg_MFprops.femmine,family=binomial)
summary(fit1)

#######################################################

library(glmnet)
fit=glmnet(X1.train,y.train,family="binomial")
print(fit)
