errm(list=ls())

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

sort(dati$CODICE.ZIP)[1:10]
sort(dati.info$CODICE.ZIP)[1:10]
#corrispondono quindi stai raccogliando dati sulle stesse persone
#tuttavia il dataset dati ha meno soggetti, quindi quando devo vedere differenze fra 
#M e F devo lavorare su meno dati

######################################################
#MI CONCENTRO SUI DATASET dati e dati.info (INFORMAZIONI SUI PROFILI FACEBOOK)

#lavoro su proporzione di messaggi alle F (variabile 13)
#analisi univariate
names(dati)[13]
summary(dati[,13])
sd(dati[,13])
par(mfrow=c(1,2))
boxplot(dati[,13])
hist(dati[,13],prob=T,main="proporzione di messaggi alle ragazze",xlab="",ylim=c(0,3))
lines(density(dati[,13]),lwd=2)
par(mfrow=c(1,1))
shapiro.test(dati[,13]) #accetto l'ipotesi di normalit� (pvalue >0.05)
#intervallo di confidenza al 95% dopo aver accettato la normalit�
0.5518+c(-1,1)*qnorm(0.975)*0.1426936
#poco informativo perch� ampio

#analisi bivariate (sempre sulla variabile 13 prop di mess alle F) (DIFFERENZA SIGNIFICATIVA)
#mi condiziono al sesso (quindi devo recuperare da dati.info il sesso dei soggetti corrispondenti)
names(dati.info)[5]
sex=NULL
for(i in 1:length(dati$CODICE.ZIP)){
  sex=c(sex,dati.info[dati.info$CODICE.ZIP==dati$CODICE.ZIP[i],5])
}
length(sex)  #contiene il sesso dei 324 soggetti di cui conosco i dati di facebook (contenuti in dati)
sex[1:10]
Msg.sex=data.frame(dati[,13],sex)
names(Msg.sex)=c("proporzione","sesso")
str(Msg.sex)
dim(Msg.sex)
Msg.sex[1:5,]
summary(Msg.sex$proporzione)  #univariato (uguale a sopra)
summary(Msg.sex$proporzione[Msg.sex$sesso=="M"]) 
summary(Msg.sex$proporzione[Msg.sex$sesso=="F"]) 
#commentare che ci sono ragazze che messaggiano solo con ragazze (massimo variabile = 1)
#commentare che media = mediana e quindi distribuzione simmetrica

#rappresentazione grafica distribuzione prop msg MF condizionate e marginale
par(mfrow=c(1,2))
boxplot(Msg.sex$proporzione[Msg.sex$sesso=="M"],main="Maschi",ylim=c(0,1))
boxplot(Msg.sex$proporzione[Msg.sex$sesso=="F"],main="Femmine",ylim=c(0,1))
par(mfrow=c(1,1))

#test signif differenza fra condizionata M e condizionata F
shapiro.test(Msg.sex$proporzione[Msg.sex$sesso=="M"]) #accetto normalit�
shapiro.test(Msg.sex$proporzione[Msg.sex$sesso=="F"]) #accetto normalit�
var.test(Msg.sex$proporzione[Msg.sex$sesso=="M"],Msg.sex$proporzione[Msg.sex$sesso=="F"])
#accetto anche l'omoschedasticit� (=> stessa varianza) quindi t-test
t.test(Msg.sex$proporzione[Msg.sex$sesso=="M"],Msg.sex$proporzione[Msg.sex$sesso=="F"],var.equal=T)
#i maschi hanno una proporzione di messaggi con le ragazze significativamente inferiore
#a quella delle femmine

#rappresentazione grafica densit�
plot(density(Msg.sex$proporzione[Msg.sex$sesso=="M"]),main="Proporzione di messaggi alle ragazze",xlab="")
lines(density(Msg.sex$proporzione[Msg.sex$sesso=="F"]),col=2)
legend("topleft",c("Maschi","Femmine"),lty=1,col=1:2)
#in realt�, avendo accettato la normalit�, il confronto non � fra le due densit� sopra
#ma fra queste due
mean(Msg.sex$proporzione[Msg.sex$sesso=="M"])
mean(Msg.sex$proporzione[Msg.sex$sesso=="F"])
sd(Msg.sex$proporzione[Msg.sex$sesso=="M"])
sd(Msg.sex$proporzione[Msg.sex$sesso=="F"])
curve(dnorm(x,mean=0.4691819,sd=0.1263981),main="Proporzione di messaggi alle ragazze",xlab="",ylab="")
lines(c(0.4691819,0.4691819),c(-1,dnorm(0.4691819,mean=0.4691819,sd=0.1263981)),lty=2)
curve(dnorm(x,mean=0.5717886,sd=0.139393),col=2,add=T)
lines(c(0.5717886,0.5717886),c(-1,dnorm(0.5717886,mean=0.5717886,sd=0.139393)),lty=2,col=2)
legend("topleft",c("Maschi","Femmine"),lty=1,col=1:2)

#confronto fra densit� stimata con il metodo del nucleo e densit� di una normale (ho accettato la normalit�)
plot(density(Msg.sex$proporzione[Msg.sex$sesso=="M"]),main="Proporzione di messaggi alle ragazze",xlab="",lty=2)
curve(dnorm(x,mean=0.4691819,sd=0.1263981),add=T,lwd=2)
lines(density(Msg.sex$proporzione[Msg.sex$sesso=="F"]),col=2,lty=2)
curve(dnorm(x,mean=0.5717886,sd=0.139393),col=2,add=T,lwd=2)
legend("topleft",c("Maschi","Femmine"),lty=1,col=1:2)

#lavoro su richieste di amicizia (variabile 488) (ricevute o inviate?) (DIFFERENZA M/F NON SIGNIFICATIVA)
#(non messa sulla tesi)

names(dati)[488]
summary(dati[,488])   #marginale
summary(dati[,488][sex=="M"])  #maschi
summary(dati[,488][sex=="F"])  #femmine
par(mfrow=c(1,3))
boxplot(dati[,488][sex=="M"],main="Maschi",ylim=c(0,1600))
boxplot(dati[,488][sex=="F"],main="Femmine",ylim=c(0,1600))
boxplot(dati[,488],main="Marginale",ylim=c(0,1600))
par(mfrow=c(1,1))
#posso lavorare su scala logaritmica
#per� log(0) tende a -Inf
table(dati[,488]==0)
#ci sono 35 zeri (persone che non messaggiano con ragazze)
#quindi uso trasformazione radice quadrata
par(mfrow=c(1,3))
boxplot(sqrt(dati[,488][sex=="M"]),main="Maschi",ylim=c(0,40))
boxplot(sqrt(dati[,488][sex=="F"]),main="Femmine",ylim=c(0,40))
boxplot(sqrt(dati[,488]),main="Marginale",ylim=c(0,40))
par(mfrow=c(1,1))
shapiro.test(sqrt(dati[,488][sex=="M"]))  #rifiuto normalit�
shapiro.test(sqrt(dati[,488][sex=="F"]))  #rifiuto normalit�
#quindi test basato sui ranghi (test non parametrico di Mann-Whitney)
#equivalente al t-test quando non accetto normalit�
#(interpretabile come confronto fra le mediane o confronto fra le distribuzioni)
wilcox.test(sqrt(dati[,488][sex=="M"]),sqrt(dati[,488][sex=="F"]))
#accetto, quindi le due distribuzioni condizionate non sono significativamente diverse,
#oppure dico che le mediane delle due distribuzioni non sono signif diverse
#(non serve parlare di radice quadrata della mediana perch� est basati sui ranghi sono
#invarianti rispetto a trasformazioni monotone dei dati)

#rappresentazioni grafiche (sui valori originali e sui valori trasformati)
plot(density(dati[,488][sex=="M"]),main="Richieste di amicizia",xlab="",xlim=c(0,1600))
lines(density(dati[,488][sex=="F"]),col=2)
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)
plot(density(sqrt(dati[,488][sex=="F"])),main="Richieste di amicizia (su scala radice quadrata)",xlab="",col=2)
lines(density(sqrt(dati[,488][sex=="M"])),col=1)
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)

#lavoro su freq orarie bacheca
names(dati)[499:521]  #MANCA LA FREQUENZA ALLE ORE 2
str(dati[,499:521])
summary(dati[,499:521])
#ci sono dati mancanti
idx=NULL
for(i in 1:324){
  if (is.na(dati[i,499])) idx=c(idx,i)
}
idx  #contiene le posizioni con gli NaN
plot(c(0,1,3:23),apply(dati[-idx,499:521],2,mean),xlab="ore",ylab="frequenze",type="l",main="frequenze accessi in bacheca")

#differenziando per genere
sex2=sex[-idx]
dati2=dati[-idx,499:521]
plot(c(0,1,3:23),apply(dati2[sex2=="M",],2,mean),xlab="ore",ylab="frequenze",type="l",main="frequenze accessi in bacheca")
lines(c(0,1,3:23),apply(dati2[sex2=="F",],2,mean),col=2)
legend("topleft",c("Maschi","Femmine"),lty=1,col=1:2)
#commentare il picco dei ragazzi online a met� mattina rispetto alle ragazze
#per il resto comportamento molto simile

#lavoro sul numero medio di messaggi agli amici (variabile 2)

names(dati)[2]
length(dati[,2])  #non ho dati mancanti
summary(dati[,2])  #non ho zeri (persone che non messaggiano mai)
sd(dati[,2])
par(mfrow=c(1,2))
boxplot(dati[,2],main="Su scala originale")
boxplot(log(dati[,2]),main="Su scala logaritmica")
par(mfrow=c(1,1))
table(dati[,2]>400)
prop.table(table(dati[,2]>400))
400/30
shapiro.test(log(dati[,2]))
#a parte 5 persone tutti inviano meno di 13 messaggi al giorno
#forte asimmetria positiva quindi lavoro su scala logaritmica (perch� non ho zeri)
boxplot(log(dati[,2]))
#lavoro sulla differenza fra M e F su scala logaritmica
par(mfrow=c(1,2))
boxplot(log(dati[,2][sex=="M"]),main="Maschi",ylim=c(-1,8),ylab="logaritmo del numero medio di messaggi")
boxplot(log(dati[,2][sex=="F"]),main="Femmine",ylim=c(-1,8),ylab="logaritmo del numero medio di messaggi")
par(mfrow=c(1,1))
#commento pi� valori anomali (distanti dalla mediana) nella distribuzione delle F
#distribuzione delle F con code molto pi� pesanti
shapiro.test(log(dati[,2][sex=="M"])) #accetto normalit�
shapiro.test(log(dati[,2][sex=="F"]))  #rifiuto normalit�
#faccio entrambibi i test e vedo se vanno nella stessa direzione (accetto entrambi o rifiuto entrambi)
var.test(log(dati[,2][sex=="M"]),log(dati[,2][sex=="F"]))  #accetto omoschedasticit� (anche se normalit� dubbia)
t.test(log(dati[,2][sex=="M"]),log(dati[,2][sex=="F"]),var.equal=T)  
#t-test accetta uguaglianza logaritmi delle medie
t.test(log(dati[,2][sex=="M"]),log(dati[,2][sex=="F"]))  
#test di Welch (non assumo omosched) accetta uguaglianza dei logaitmi delle medie
wilcox.test(log(dati[,2][sex=="M"]),log(dati[,2][sex=="F"]))
wilcox.test(dati[,2][sex=="M"],dati[,2][sex=="F"])  #sono uguali
#accetta uguaglianza fra le distribuzioni e fra le mediane
#(test non parametrico invariante rispetto a trasformazioni monotone dei dati, 
#esempio trasformata logaritmica o radice quadrata)
#quindi le distribuzioni (e i logaritmi delle medie) non sono signif diverse fra M e F
#M e F mandano lo stesso numero di messaggi
plot(density(dati[,2][sex=="M"]),main="Numero medio di messaggi",xlab="",xlim=c(0,2187),ylim=c(0,0.02))
lines(density(dati[,2][sex=="F"]),col=2)
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)
plot(density(log(dati[,2][sex=="M"])),main="Numero medio di messaggi (su scala logaritmica)",xlab="",xlim=c(-0.5,8),ylim=c(0,0.45))
lines(density(log(dati[,2][sex=="F"])),col=2)
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)
lines(c(median(log(dati[,2][sex=="M"])),median(log(dati[,2][sex=="M"]))),c(0,0.33),lty=2)
lines(c(median(log(dati[,2][sex=="F"])),median(log(dati[,2][sex=="F"]))),c(0,0.425),lty=2,col=2)

#lavoro sulla variabile 4 (non messa sulla tesi)

names(dati)[4]
summary(dati[,4])  #non ho zeri
boxplot(dati[,4])  #forte asimmetria positiva
#quindi scelgo di trasformare la variabile (log perch� non ho zeri)
boxplot(log(dati[,4]))
#analisi bivariate
shapiro.test(log(dati[,4][sex=="M"]))  #accetto normalit�
shapiro.test(log(dati[,4][sex=="F"]))   #rifiuto normalit�
#test grafico (diagramma quantile-quantile) per la verifica della normalit�
qqnorm(log(dati[,4][sex=="F"]))
qqline(log(dati[,4][sex=="F"]))
#c'� un allontanamento sistematico nelle code, quindi rifiuto normalit� per code pesanti
boxplot(log(dati[,4][sex=="F"]))

#quindi nei maschi accetto normalit�, nelle femmine rifiuto. faccio sia i test parametrici
#sia quelli non paranetrici per sicurezza
t.test(log(dati[,4][sex=="M"]),log(dati[,4][sex=="F"]))  #accetto uguaglianza in media
wilcox.test(dati[,4][sex=="M"],dati[,4][sex=="F"])  #accetto uguaglianza in distribuzione (uguaglianza mediane)
#i test parametrici e quelli non parametrici danno risultati coerenti => no differenza significativa

#confronto grafico
plot(density(dati[,4][sex=="F"]),main="Numero medio di caratteri per messaggio",xlab="",xlim=c(430,4000000),col=2)
lines(density(dati[,4][sex=="M"]))
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)
plot(density(log(dati[,4][sex=="F"])),main="Numero medio di caratteri per messaggio (su scala logaritmica)",xlab="",xlim=c(6,17),col=2)
lines(density(log(dati[,4][sex=="M"])))
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)

#variabile 8

names(dati)[8]
summary(dati[,8])  
sd(dati[,8])
mean(dati[,8])/30
par(mfrow=c(1,2))
boxplot(dati[,8]) 
hist(dati[,8],prob=T)
par(mfrow=c(1,1))
shapiro.test(dati[,8])
par(mfrow=c(1,2))
boxplot(dati[,8][sex=="M"],main="Maschi",ylim=c(20,160)) 
boxplot(dati[,8][sex=="F"],main="Femmine",ylim=c(20,160)) 
par(mfrow=c(1,1))
shapiro.test(dati[,8][sex=="M"])  #rifiuto normalit�
shapiro.test(dati[,8][sex=="F"])   #rifiuto normalit�
wilcox.test(dati[,8][sex=="M"],dati[,8][sex=="F"])  
#rifiuto uguaglianza in distribuzione 
#quindi le femmine scrivono messaggi mediamente pi� lunghi
#confronto grafico
plot(density(dati[,8][sex=="F"]),main="Numero medio di caratteri per messaggio",xlab="",xlim=c(0,200),col=2)
lines(density(dati[,8][sex=="M"]))
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)
lines(c(median(dati[,8][sex=="M"]),median(dati[,8][sex=="M"])),c(0,0.026),lty=2)
lines(c(median(dati[,8][sex=="F"]),median(dati[,8][sex=="F"])),c(0,0.027),lty=2,col=2)

#lavoro sulla variabile 529 (non messa sulla tesi)

names(dati)[529]
summary(dati[,529])  
boxplot(dati[,529])  #distriobuzione abbastanza simmetrica
shapiro.test(dati[,529][sex=="M"])  #rifiuto normalit� al 5% (potrei accettare all 1%)
shapiro.test(dati[,529][sex=="F"])   #rifiuto normalit�
#allora rifiuto per entrambi la normalit� e faccio test basato sui ranghi
wilcox.test(dati[,529][sex=="M"],dati[,529][sex=="F"])  #accetto uguaglianza in distribuzione (uguaglianza mediane)
#confronto grafico
plot(density(dati[,529][sex=="F"]),main="Numero medio di caratteri per messaggio",xlab="",xlim=c(0,351),col=2)
lines(density(dati[,529][sex=="M"]))
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)

###############################################
#MI CONCENTRO SUI TEST ATTITUDINALI (DATASET dati.testAtt)

names(dati.testAtt)
dim(dati.testAtt)[1]
length(unique(dati.testAtt$CODICE.ZIP)) #due CODICE.ZIP ripetuti
table(dati.testAtt$CODICE.ZIP)[table(dati.testAtt$CODICE.ZIP)>1]
dati.testAtt[dati.testAtt$CODICE.ZIP=="CODICE_REDATTO",10:15]
dati.testAtt[dati.testAtt$CODICE.ZIP=="CODICE_REDATTO",10:15]
#ci sono due righe con uguale codice zip e diversi punteggi nei test attitudinali
#non sapendo quale riga � quella corretta, e quindi quale punteggio attribuire 
#al soggetto con quel codice zip, faccio una media dei due punteggi
#sovrascrivo la media su una delle due righe
str(dati.testAtt) #per fare la media devo togliere i fattori dal calcolo
names(dati.testAtt) #devo togliere le colonne 1, 35,..,63
dati.testAtt[164,2:34]=apply(dati.testAtt[c(164,965),2:34],2,mean)
dati.testAtt[dati.testAtt$CODICE.ZIP=="CODICE_REDATTO",10:15]  #ora la 164 contiene le medie dei punteggi
dati.testAtt=dati.testAtt[-965,]  #elimino la riga 965
dati.testAtt[330,2:34]=apply(dati.testAtt[c(330,913),2:34],2,mean)
dati.testAtt[dati.testAtt$CODICE.ZIP=="CODICE_REDATTO",10:15] #ora la 330 contiene le medie dei punteggi
dati.testAtt=dati.testAtt[-913,]  #elimino la riga 913
dim(dati.testAtt)[1]
length(unique(dati.testAtt$CODICE.ZIP))  #ora i codici sono univoci

#mi concentro su queste 5 variabili
names(dati.testAtt)[c(11,12,13,15,34)]
summary(dati.testAtt[,c(11,12,13,15,34)])
#sembrerebbero tutte su scala da 0 a 5

idx11=NULL
for(i in 1:1420){
  if (is.na(dati.testAtt[i,11])) idx11=c(idx11,i)
}
length(idx11) 
idx11[1:5]   #contiene le posizioni con gli NaN sulla colonna 11
idx12=NULL
for(i in 1:1420){
  if (is.na(dati.testAtt[i,12])) idx12=c(idx12,i)
}
length(idx12) 
idx12[1:5]   #contiene le posizioni con gli NaN sulla colonna 11 (diversida idx11)
idx13=NULL
for(i in 1:1420){
  if (is.na(dati.testAtt[i,13])) idx13=c(idx13,i)
}
length(idx13) 
idx13[1:5]  #sembrano gli stessi di idx12  
idx15=NULL
for(i in 1:1420){
  if (is.na(dati.testAtt[i,15])) idx15=c(idx15,i)
}
length(idx15) 
idx15[1:5]  #sembrano gli stessi di idx12  
idx34=NULL
for(i in 1:1420){
  if (is.na(dati.testAtt[i,34])) idx34=c(idx34,i)
}
length(idx34) 
idx34[1:5]  

#vedo quante righe hanno almeno un Nan
length(unique(c(idx11,idx12,idx13,idx15,idx34)))
sort(unique(c(idx11,idx12,idx13,idx15,idx34)))  #sono le righe che vado a togliere
dati.testAtt2=dati.testAtt[-sort(unique(c(idx11,idx12,idx13,idx15,idx34))),]
dim(dati.testAtt)
dim(dati.testAtt2)

summary(dati.testAtt2[,c(11,12,13,15,34)])  #non ho pi� Nan

#analisi univariate sulle 5 variabili
shapiro.test(dati.testAtt2[,11])
shapiro.test(dati.testAtt2[,12])
shapiro.test(dati.testAtt2[,13])
shapiro.test(dati.testAtt2[,15])
shapiro.test(dati.testAtt2[,34])
#rifiuto la normalit� su tutti

hist(dati.testAtt2[,11],xlab="social",main="",prob=T,col="grey")
hist(dati.testAtt2[,12],xlab="openess",main="",prob=T,col="grey")
#molte persone risultano con valori bassi di openess
hist(dati.testAtt2[,13],xlab="emotional",main="",prob=T,col="grey")
hist(dati.testAtt2[,15],xlab="extraversion",main="",prob=T,col="grey")
prop.table(table(dati.testAtt2[,15]<2.5))
#il 63.8% ha valori inferiori a 2.5
#quindi molte persone sono poco estroverse
hist(dati.testAtt2[,34],xlab="autostima",main="",prob=T,col="grey")
prop.table(table(dati.testAtt2[,34]>2.5))
#l'80% ha varori di autostima maggiori di 2.5 (valore a met� della scala)
prop.table(table(dati.testAtt2[,34]>3))
#quasi met� delle persone ha punteggi sopra al 3
#quindi la maggior parte delle persone ha un'autostima elevata di s�

#analisi bivariate 
#utlizzo la correlazione non parametrica di Spearman basata sui ranghi (perch� rifiutato normalit�)
cor(dati.testAtt2[,c(11,12,13,15,34)],method="spearman")
library(corrplot)
corrplot(cor(dati.testAtt2[,c(11,12,13,15,34)],method="spearman"),method="ellipse",diag=F,tl.pos="lt",tl.col=1,tl.cex=0.4,
         number.digits=3,addCoef.col="black",number.cex=0.6)
#dal grafico si nota che le variabili della stessa sezione (sezione H) 
#sono correlate positivamente fra di loro e negativamente con le variabili 
#delle altre sezioni. Tutte le correlazioni non sono particolarmente forti

#test basati sui ranghi per vedere la significativit� delle correlazioni
cor.test(dati.testAtt2[,13],dati.testAtt2[,34],method="spearman")
#la correlazione negativa fra emotional e autostima � significativa
cor.test(dati.testAtt2[,12],dati.testAtt2[,15],method="spearman")
#la correlazione positiva fra openess e extraversion � significativa
cor.test(dati.testAtt2[,11],dati.testAtt2[,13],method="spearman")
cor.test(dati.testAtt2[,11],dati.testAtt2[,34],method="spearman")
#le uniche due correlazioni risultate positive fra variabili di sezioni diverse 
#non sono risultate significative

#UNISCO LE INFORMAZIONI DI dati.testAtt E DI dati.info

#confronto i punteggi dei test fra maschi e femmine (solo per i 345 soggetti di cui ho informazioni)
#salvo le posizioni riga dei CODICE.ZIP di cui conosco anche il sesso
sex.test=NULL
idx.test=NULL
for(i in 1:dim(dati.info)[1]){
  for(j in 1:dim(dati.testAtt2)[1]){
    if (dati.info$CODICE.ZIP[i]==dati.testAtt2$CODICE.ZIP[j]){
      sex.test=c(sex.test,dati.info$sesso[i])
      idx.test=c(idx.test,j)
    }
  }
}
length(sex.test)
table(sex.test)  
#le persone per cui ho la corrispondenza fra il codice.zip di dati.info
#e i codici.zip dei test attitudinali sono quasi tutte femmine
sex.test[1:10]
length(idx.test)
idx.test[1:10]
dati.testAtt3=data.frame(sex.test,dati.testAtt2[idx.test,c(11,12,13,15,34)])
str(dati.testAtt3)
head(dati.testAtt3)
summary(dati.testAtt3) #ci sono due persone di cui non conosco il sesso 
idx.test3=NULL
for(i in 1:dim(dati.testAtt3)[1]){
  if (is.na(dati.testAtt3$sex.test[i])) idx.test3=c(idx.test3,i)
}
idx.test3 
dati.testAtt3=dati.testAtt3[-idx.test3,]  #tolgo le due righe di cui non conosco il sesso

#vedo se ci sono differenze fra maschi e femmine

#social
par(mfrow=c(1,2))
hist(dati.testAtt3$E_social[sex.test=="M"],xlab="social",main="Maschi",prob=T)
hist(dati.testAtt3$E_social[sex.test=="F"],xlab="social",main="Femmine",prob=T)
par(mfrow=c(1,1))
shapiro.test(dati.testAtt3$E_social[dati.testAtt3$sex.test=="M"])  #rifiuto normalit�
shapiro.test(dati.testAtt3$E_social[dati.testAtt3$sex.test=="F"])  #rifiuto normalit�
plot(density(dati.testAtt3$E_social[dati.testAtt3$sex.test=="M"]),xlab="social",main="")
lines(density(dati.testAtt3$E_social[dati.testAtt3$sex.test=="F"]),col=2)
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)
#verifico se la differenza � significativa (test non parametrico)
wilcox.test(dati.testAtt3$E_social[dati.testAtt3$sex.test=="M"],dati.testAtt3$E_social[dati.testAtt3$sex.test=="F"])
#accetto uguaglianza in distribuzione, differenza non significativa

#openess
par(mfrow=c(1,2))
hist(dati.testAtt3$H_openess[sex.test=="M"],xlab="openess",main="Maschi",prob=T)
hist(dati.testAtt3$H_openess[sex.test=="F"],xlab="openess",main="Femmine",prob=T)
par(mfrow=c(1,1))
shapiro.test(dati.testAtt3$H_openess[dati.testAtt3$sex.test=="M"])  #accetto normalit� (al 5%)
shapiro.test(dati.testAtt3$H_openess[dati.testAtt3$sex.test=="F"])  #rifiuto normalit�
plot(density(dati.testAtt3$H_openess[dati.testAtt3$sex.test=="M"]),xlab="openess",main="",ylim=c(0,0.7))
lines(density(dati.testAtt3$H_openess[dati.testAtt3$sex.test=="F"]),col=2)
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)
wilcox.test(dati.testAtt3$H_openess[dati.testAtt3$sex.test=="M"],
            dati.testAtt3$H_openess[dati.testAtt3$sex.test=="F"])
#accetto uguaglianza in distribuzione, differenza non significativa

#emotional (DIFFERENZA SIGNIFICATIVA)
par(mfrow=c(1,2))
hist(dati.testAtt3$H_emotional[sex.test=="M"],xlab="emotional",main="Maschi",prob=T)
hist(dati.testAtt3$H_emotional[sex.test=="F"],xlab="emotional",main="Femmine",prob=T)
par(mfrow=c(1,1))
shapiro.test(dati.testAtt3$H_emotional[dati.testAtt3$sex.test=="M"])  #rifiuto normalit� (al 5%)
shapiro.test(dati.testAtt3$H_emotional[dati.testAtt3$sex.test=="F"])  #rifiuto normalit�
plot(density(dati.testAtt3$H_emotional[dati.testAtt3$sex.test=="M"]),xlab="emotional",main="",ylim=c(0,0.5))
lines(density(dati.testAtt3$H_emotional[dati.testAtt3$sex.test=="F"]),col=2)
legend("topleft",c("Maschi","Femmine"),lty=1,col=1:2)
lines(c(median(dati.testAtt3$H_emotional[dati.testAtt3$sex.test=="M"]),median(dati.testAtt3$H_emotional[dati.testAtt3$sex.test=="M"])),
      c(0,0.42),lty=2)
lines(c(median(dati.testAtt3$H_emotional[dati.testAtt3$sex.test=="F"]),median(dati.testAtt3$H_emotional[dati.testAtt3$sex.test=="F"])),
      c(0,0.43),lty=2,col=2)
wilcox.test(dati.testAtt3$H_emotional[dati.testAtt3$sex.test=="M"],
            dati.testAtt3$H_emotional[dati.testAtt3$sex.test=="F"])
#rifiuto l'uguaglianza in distribuzione, la distribuzione condizionata delle femmine 
#� spostata verso valori mediamente pi� elevati (risultano pi� emotive dei maschi)

#extraversion
par(mfrow=c(1,2))
hist(dati.testAtt3$H_extraversion[sex.test=="M"],xlab="extraversion",main="Maschi",prob=T)
hist(dati.testAtt3$H_extraversion[sex.test=="F"],xlab="extraversion",main="Femmine",prob=T)
par(mfrow=c(1,1))
shapiro.test(dati.testAtt3$H_extraversion[dati.testAtt3$sex.test=="M"])  #rifiuto normalit�
shapiro.test(dati.testAtt3$H_extraversion[dati.testAtt3$sex.test=="F"])  #rifiuto normalit�
plot(density(dati.testAtt3$H_extraversion[dati.testAtt3$sex.test=="M"]),xlab="extraversion",main="",ylim=c(0,0.7))
lines(density(dati.testAtt3$H_extraversion[dati.testAtt3$sex.test=="F"]),col=2)
legend("topright",c("Maschi","Femmine"),lty=1,col=1:2)
wilcox.test(dati.testAtt3$H_extraversion[dati.testAtt3$sex.test=="M"],
            dati.testAtt3$H_extraversion[dati.testAtt3$sex.test=="F"])
#accetto uguaglianza in distribuzione, differenza non significativa

#autostima
par(mfrow=c(1,2))
hist(dati.testAtt3$autostima[sex.test=="M"],xlab="autostima",main="Maschi",prob=T)
hist(dati.testAtt3$autostima[sex.test=="F"],xlab="autostima",main="Femmine",prob=T)
par(mfrow=c(1,1))
shapiro.test(dati.testAtt3$autostima[dati.testAtt3$sex.test=="M"])  #rifiuto normalit�
shapiro.test(dati.testAtt3$autostima[dati.testAtt3$sex.test=="F"])  #rifiuto normalit�
plot(density(dati.testAtt3$autostima[dati.testAtt3$sex.test=="M"]),xlab="autostima",main="",ylim=c(0,0.7))
lines(density(dati.testAtt3$autostima[dati.testAtt3$sex.test=="F"]),col=2)
legend("topleft",c("Maschi","Femmine"),lty=1,col=1:2)
lines(c(median(dati.testAtt3$autostima[dati.testAtt3$sex.test=="M"]),median(dati.testAtt3$autostima[dati.testAtt3$sex.test=="M"])),
      c(0,0.6),lty=2)
lines(c(median(dati.testAtt3$autostima[dati.testAtt3$sex.test=="F"]),median(dati.testAtt3$autostima[dati.testAtt3$sex.test=="F"])),
      c(0,0.72),lty=2,col=2)
wilcox.test(dati.testAtt3$autostima[dati.testAtt3$sex.test=="M"],
            dati.testAtt3$autostima[dati.testAtt3$sex.test=="F"])
#al 5% accetto l'uguaglianza in distribuzione, se lavoro invece con alfa fissato al 10%
#rifiuto l'uguaglianza in distribuzione. Si nota che la distribuzione condizionata delle 
#femmine si posiziona su livelli leggermente inferiori di autostima

#######################################
#CONFRONTO FRA TEST ATTITUDINALI E DATI FACEBOOK
#es numero di messaggi e autostima
#es prop mess alle F e autostima
#...

#########################################
#modello di regressione per il sesso
#variabili significative: 
#propMessaggi (var 13), 
#numero medio di caratteri per messaggio (var 8),
#emotional (var 13),
#autostima (var 34)

dati.glm=data.frame(dati.testAtt2$CODICE.ZIP[idx.test],sex.test,dati.testAtt2[idx.test,c(13,34)],rep(NA,335),rep(NA,335))
dati[,c(8,13)]
for(i in 1:dim(dati.glm)[1]){
  for(j in 1:dim(dati)[1]){
    if (dati.glm[i,1]==dati$CODICE.ZIP[j]){
      dati.glm[i,5]=dati[j,8]
      dati.glm[i,6]=dati[j,13]
    }
  }
}

summary(dati.glm)
dati.glm=dati.glm[!is.na(dati.glm[,2]),]
summary(dati.glm)
dati.glm=dati.glm[!is.na(dati.glm[,5]),]
summary(dati.glm)

names(dati.glm)=c("CODICE.ZIP","sesso","emotional","autostima","caratteri","propmsg")
head(dati.glm)
#codice serve solo per unire i dataset diversi
#sesso � la risposta (varibile dicotomica => modello logistico) 
#le altre variabili sono i regressori
str(dati.glm)

fit=glm(dati.glm$sesso~dati.glm$emotional+dati.glm$autostima+dati.glm$caratteri+dati.glm$propmsg,family=binomial)
summary(fit)
#autostima e caratteri non sono significative
#comincio togliendo quella pi� non significativa ovvero autostima
fit2=update(fit,.~.-dati.glm$autostima)
summary(fit2)
#caratteri rimane non significativa quindi la tolgo
fit3=update(fit2,.~.-dati.glm$caratteri)
summary(fit3)
#bont� di adattamento
W=278.94-251.14
1-pchisq(W,305-303)
#viene un pvalue piccolo quindi rifiuto il modello con la sola intercetta 
#(che il tuo modello � meglio del modello nullo)
contrasts(dati.glm$sesso)  #codificato 1 maschio 0 femmina
table(dati.glm$sesso,fitted(fit3)>0.5)
(252+3)/306  #indice di accuratezza 
252/254
3/52
#l'83% del tuo campione viene classificato correttamente
library(pROC)
plot(roc(dati.glm$sesso,fitted(fit3)),legacy.axes=T,print.auc=T,asp=F)
#lettura auc:
#>0.8 molto buono
#0.6 < < 0.8 discreto
#<0.6 schifo (l'auc � nel pegiore dei casi 0.5)
#il modello ha una discreta capacit� predittiva

#commento: accuratezza e auc discreti, tuttavia il modello si adatta benissimo sul gruppo delle ragazze
#ma si adatta molto male nel gruppo dei ragazzi

###############################################################################################
#creo dataset unico per usare la funzione step

#dati: informazione attivit� facebook (righe 324)
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

merge.dati$CODICE.ZIP=NULL  #elimina la colonna (se si fa dim(merge.dati) c'� una colonna in meno)
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
j  #sesso � la variabile 533
X=merge.dati[,-j]   #matrice delle esplicative

dim(merge.dati)
dim(X)
#ho 324 osservazioni: 70 per l'insieme di test e 324-70 per l'insieme di allenamento del modello
set.seed(50)   #serve per generare sempre gli stessi numeri
idx=sample(1:nrow(merge.dati), 70)  #non usare trunc runif altrimenti potrebbe estrarre due volte la stessa riga
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

#############################################################################################################

std <- function(x){
  return((x - mean(x))/sd(x))
}
#OSS: il prof lavora sui dati standardizzati

x <- model.matrix(~., data = X.train)
library(leaps)


fit0=glm(y.train~1,family=binomial)
summary(fit0)

x=model.matrix(~.,data=X.train)
dim(x)
colnames(x)

x1=model.matrix(~.,data=X1.train)
dim(x1)
colnames(x1)

f1 <- as.formula(paste("y.train ~", paste(colnames(x1)[-1], collapse = "+")))
f1

attach(X.train)
step(fit0,direction="both",scope=f1)

flag=rep(NA,dim(X1.train)[2])
for(i in 1:dim(X1.train)[2]){
  flag[i]=all(is.na(X1.train[,i]))
}
table(flag)  #non ho colonne vuote

m1 <- leaps(x, y.train, int = FALSE) 

#la risposta non pu� essere di tipo factor (?) -> la trasformo in numerica
y.train[1:10]
y.train=as.numeric(y.train)-1  #codifica con 1=M e 0=F
str(y.train)
fitT=glm(y.train~.,data=X.train,family=binomial)
formula(fitT)


#m1 <- leaps(x, y.train, int = FALSE)   #non funziona perch� ho troppe variabili
#leaps(X.train,y.train)
#plot(m1$size, m1$Cp)

#provo a farne le componenti principali per ridurre la dimensionalit�
#pc <- princomp(x[, -1])  #si pu� usare solo quando ci sono pi� unit� che variabili
#summary(pc)
#screeplot(pc, type = "l")

?regsubsets
str(X.train)
model=regsubsets(as.matrix(X.train),y.train)

dim(X.train)
pos=rep(NA,597)
for(i in 1:597){
  pos[i]=is.numeric(X.train[,i])
}
table(pos)
str(X.train[,!pos])  #sono le variabili non numeriche presenti nel dataset
#hanno tutte tanti livelli, le tolgo dal dataset
X1.train=X.train[,pos]
dim(X1.train)
#597-17=580

pos=rep(NA,580)
for(i in 1:580){
  pos[i]=length(unique(X1.train[,i]))==1  #sono le variabili che assumono valore costante in tutte le unit�
}
table(pos)  #sono 31
str(X1.train[,pos])   #sono parole che nessuno di questi 254 soggetti ha mai utilizzato
X1.train=X1.train[,!pos]
dim(X1.train)
#580-31=549

?prcomp
?svd

str(X1.train)
X1.train=as.matrix(X1.train)   #pc e svd richiedono in input una matrice non un dataframe

inv=scale(X1.train)
pos=rep(NA,549)
posj=rep(NA,254)
for(j in 1:549){
  for(i in 1:254){
    posj[i]=is.na(inv[i,j])
  }
  pos[j]=all(posj)
}
table(pos) #ci sono 8 colonne nulle, quindi ci sono 8 colonne originali che assumono solo valore 0
str(as.data.frame(X1.train)[,pos])
dim(X1.train)
X1.train=X1.train[,!pos]
dim(X1.train)
#549-8=541

inv=scale(X1.train)
pos=rep(NA,541)
posj=rep(NA,254)
for(j in 1:541){
  for(i in 1:254){
    posj[i]=is.infinite(inv[i,j])
  }
  pos[j]=all(posj)
}
table(pos)  #non ci sono colonne con valori infiniti

pc=prcomp(X1.train)
svd(X1.train)

#############################################################################################################

#modelli

fit41=glm(y.train~.,family=binomial,data=X.train[,1:100])
step(fit41)
fit41f=glm(formula = y.train ~ msg_nchar_stats.nchar_per_text.Median + 
             msg_MFprops.femmine + msg_freq_user.freqFriend1 + msg_freq_user.freqFriend2 + 
             msg_freq_ore.03 + msg_freq_ore.04 + msg_freq_ore.07 + msg_freq_ore.15 + 
             msg_freq_ore.16 + msg_freq_ore.17 + msg_freq_ore.18 + user_grp.esclamativo + 
             user_grp.EMOTEGOOD + user_grp.EMOTEZZZ + user_grp.EMOTESIII + 
             user_grp.EMOTENOOO + user_grp.EMOTEOHOH + user_grp.EMOTEAZZ + 
             user_grp.EMOTEOOO + user_grp.EMOTESOS + user_grp.EMOTEWOW + 
             user_grp.sicuro + user_grp.scusa + user_grp.dispiace + user_grp.disturbo + 
             user_grp.dimmi + user_grp.male, family = binomial, data = X.train[,1:100])

fit42=glm(y.train~.,family=binomial,data=X.train[,101:200])
step(fit42)
fit42f=glm(formula = y.train ~ user_grp.lui + user_grp.lei + user_grp.loro + 
             user_grp.voi + user_grp.nervoso + user_grp.triste + user_grp.interessa + 
             user_grp.secondoMe + user_grp.secondoTe + user_grp.nonRiesco + 
             user_grp.riesco + user_grp.impazzi + user_grp.preoccupato + 
             user_grp.incubo + user_grp.aspettare + user_grp.pensare + 
             user_grp.scocciare + user_grp.stufo + user_grp.conto + user_grp.pazienza + 
             user_grp.consapevole + user_grp.chePalle + user_grp.importa + 
             user_grp.nonImporta + user_grp.frustrante + user_grp.merito + 
             user_grp.colpa + user_grp.disperato + user_grp.conseguenza + 
             user_grp.causa + user_grp.perdono + user_grp.sento + user_grp.senti + 
             user_grp.comeSenti + user_grp.si + user_grp.no + user_grp.niente + 
             user_grp.assolutamente + user_grp.tu + user_personal.domanda + 
             user_personal.esclamativo + user_personal.virgole_punti + 
             user_personal.EMOTEGOOD + user_personal.EMOTELOVE + user_personal.EMOTEBAD + 
             user_personal.EMOTEWINK + user_personal.EMOTESHOCK + user_personal.EMOTEAMAZE + 
             user_personal.EMOTEZZZ + user_personal.EMOTESIII + user_personal.EMOTEAHHH + 
             user_personal.EMOTEEHHH + user_personal.EMOTEOHOH + user_personal.EMOTEIHIH + 
             user_personal.EMOTEAHAH + user_personal.EMOTEEHEH + user_personal.EMOTEAZZ + 
             user_personal.EMOTEDAIII + user_personal.cazzo + user_personal.cazzata + 
             user_personal.merda + user_personal.EMOTEAAA + user_personal.EMOTEOOO + 
             user_personal.EMOTEEEE + user_personal.EMOTESOS + user_personal.EMOTEBASTA + 
             user_personal.EMOTEWOW + user_personal.bello + user_personal.sicuro + 
             user_personal.NonLoSo + user_personal.boh + user_personal.bho + 
             user_personal.aiuto + user_personal.agitat + user_personal.ansia + 
             user_personal.giusto + user_personal.scusa + user_personal.dispiace + 
             user_personal.ascolto, family = binomial, data = X.train[,101:200])

fit43=glm(y.train~.,family=binomial,data=X.train[,201:300])
step(fit43)
fit43f=glm(formula = y.train ~ user_personal.capisco + user_personal.disturbo + 
             user_personal.dimmi + user_personal.bene + user_personal.male + 
             user_personal.ok + user_personal.mai + user_personal.sempre + 
             user_personal.impossibile + user_personal.io + user_personal.lui + 
             user_personal.lei + user_personal.loro + user_personal.voi + 
             user_personal.nervoso + user_personal.triste + user_personal.interessa + 
             user_personal.secondoMe + user_personal.secondoTe + user_personal.vicino + 
             user_personal.umore + user_personal.nonRiesco + user_personal.riesco + 
             user_personal.giuMorale + user_personal.impazzi + user_personal.angoscia + 
             user_personal.oppresso + user_personal.preoccupato + user_personal.sensibile + 
             user_personal.incubo + user_personal.aspettare + user_personal.pensare + 
             user_personal.infastidire + user_personal.scocciare + user_personal.esasperato + 
             user_personal.pezzi + user_personal.stufo + user_personal.accorgersi + 
             user_personal.conto + user_personal.pazienza + user_personal.consapevole + 
             user_personal.scrupoloso + user_personal.sensato + user_personal.responsabile + 
             user_personal.inconsciente + user_personal.chePalle + user_personal.importa + 
             user_personal.NonMImporta + user_personal.nonImporta + user_personal.frustrante + 
             user_personal.merito + user_personal.colpa + user_personal.disperato + 
             user_personal.sopportare + user_personal.conseguenza + user_personal.causa + 
             user_personal.perdono + user_personal.sento + user_personal.comeSento + 
             user_personal.senti + user_personal.comeSenti + user_personal.si + 
             user_personal.no + user_personal.niente + user_personal.assolutamente + 
             user_personal.tu + others_grp.domanda + others_grp.esclamativo + 
             others_grp.virgole_punti + others_grp.EMOTEGOOD + others_grp.EMOTELOVE + 
             others_grp.EMOTEBAD + others_grp.EMOTEWINK + others_grp.EMOTESHOCK + 
             others_grp.EMOTEAMAZE + others_grp.EMOTEZZZ + others_grp.EMOTESIII + 
             others_grp.EMOTENOOO + others_grp.EMOTEAHHH + others_grp.EMOTEEHHH + 
             others_grp.EMOTEOHOH + others_grp.EMOTEIHIH + others_grp.EMOTEAHAH + 
             others_grp.EMOTEEHEH + others_grp.EMOTEAZZ + others_grp.EMOTEDAIII + 
             others_grp.cazzo + others_grp.cazzata + others_grp.merda + 
             others_grp.EMOTEAAA + others_grp.EMOTEOOO + others_grp.EMOTEEEE + 
             others_grp.EMOTELOL + others_grp.EMOTESOS + others_grp.EMOTEBASTA + 
             others_grp.EMOTEWOW + others_grp.bello + others_grp.sicuro + 
             others_grp.NonLoSo, family = binomial, data = X.train[, 201:300])

fit44=glm(y.train~.,family=binomial,data=X.train[,301:400])
step(fit44)
fit44f=glm(formula = y.train ~ others_grp.boh + others_grp.agitat + 
             others_grp.giusto + others_grp.scusa + others_grp.disturbo + 
             others_grp.dimmi + others_grp.bene + others_grp.sempre + 
             others_grp.lei + others_grp.loro + others_grp.nervoso + others_grp.interessa + 
             others_grp.secondoMe + others_grp.vicino + others_grp.preoccupato + 
             others_grp.pensare + others_grp.esasperato + others_grp.stufo + 
             others_grp.conto + others_grp.responsabile + others_grp.inconsciente + 
             others_grp.importa + others_grp.disperato + others_grp.sopportare + 
             others_grp.perdono + others_grp.sento + others_grp.no + others_grp.niente + 
             others_personal.domanda + others_personal.EMOTEGOOD + others_personal.EMOTEBAD + 
             others_personal.EMOTEWINK + others_personal.EMOTEEHHH + others_personal.EMOTEEHEH + 
             others_personal.EMOTEAZZ + others_personal.cazzo + others_personal.cazzata, 
           family = binomial, data = X.train[, 301:400])

fit45=glm(y.train~.,family=binomial,data=X.train[,401:500])
step(fit45)
fit45f=glm(formula = y.train ~ others_personal.EMOTEAAA + others_personal.EMOTEOOO + 
             others_personal.EMOTEEEE + others_personal.EMOTELOL + others_personal.EMOTESOS + 
             others_personal.EMOTEBASTA + others_personal.EMOTEWOW + others_personal.bello + 
             others_personal.sicuro + others_personal.NonLoSo + others_personal.boh + 
             others_personal.bho + others_personal.aiuto + others_personal.agitat + 
             others_personal.ansia + others_personal.giusto + others_personal.scusa + 
             others_personal.dispiace + others_personal.ascolto + others_personal.disturbo + 
             others_personal.dimmi + others_personal.bene + others_personal.male + 
             others_personal.ok + others_personal.mai + others_personal.sempre + 
             others_personal.impossibile + others_personal.io + others_personal.lui + 
             others_personal.lei + others_personal.loro + others_personal.voi + 
             others_personal.nervoso + others_personal.triste + others_personal.interessa + 
             others_personal.secondoMe + others_personal.secondoTe + others_personal.vicino + 
             others_personal.umore + others_personal.nonRiesco + others_personal.riesco + 
             others_personal.giuMorale + others_personal.impazzi + others_personal.angoscia + 
             others_personal.oppresso + others_personal.preoccupato + 
             others_personal.sensibile + others_personal.incubo + others_personal.aspettare + 
             others_personal.pensare + others_personal.infastidire + others_personal.scocciare + 
             others_personal.esasperato + others_personal.pezzi + others_personal.stufo + 
             others_personal.accorgersi + others_personal.conto + others_personal.pazienza + 
             others_personal.consapevole + others_personal.scrupoloso + 
             others_personal.sensato + others_personal.responsabile + 
             others_personal.inconsciente + others_personal.chePalle + 
             others_personal.importa + others_personal.NonMImporta + others_personal.nonImporta + 
             others_personal.frustrante + others_personal.merito + others_personal.colpa + 
             others_personal.disperato + others_personal.sopportare + 
             others_personal.conseguenza + others_personal.causa + others_personal.perdono + 
             others_personal.sento + others_personal.comeSento + others_personal.senti + 
             others_personal.si + others_personal.no + others_personal.niente + 
             others_personal.assolutamente + others_personal.tu + wall_azioni.w_amicizia + 
             wall_azioni.w_stato + wall_azioni.w_piace + wall_azioni.w_condiviso + 
             wall_azioni.w_linkAltri + wall_azioni.w_linkTuo + wall_azioni.w_partecipato + 
             wall_azioni.w_postInBacheca + wall_azioni.w_aggiornImgProf + 
             wall_azioni.w_nuovaFoto + wall_azioni.w_postTotali + wall_freq_ore.00 + 
             wall_freq_ore.01 + wall_freq_ore.03, family = binomial, data = X.train[,401:500])

fit46=glm(y.train~.,family=binomial,data=X.train[,c(528,536:540,542:562,568,569,571,575,577,593:597)])
step(fit46)
fit46f=glm(formula = y.train ~ wall_n_days_active + H_openess + H_emotional + H_agreebleness + 
             I_emotional_regulation + z1 + z7 + z8 + M_neg + M_csc, family = binomial, 
           data = X.train[,c(528,536:540,542:562,568,569,571,575,577,593:597)])

fit5=glm(formula = y.train ~ msg_nchar_stats.nchar_per_text.Median + 
           msg_MFprops.femmine + msg_freq_user.freqFriend1 + msg_freq_user.freqFriend2 + 
           msg_freq_ore.03 + msg_freq_ore.04 + msg_freq_ore.07 + msg_freq_ore.15 + 
           msg_freq_ore.16 + msg_freq_ore.17 + msg_freq_ore.18 + user_grp.esclamativo + 
           user_grp.EMOTEGOOD + user_grp.EMOTEZZZ + user_grp.EMOTESIII + 
           user_grp.EMOTENOOO + user_grp.EMOTEOHOH + user_grp.EMOTEAZZ + 
           user_grp.EMOTEOOO + user_grp.EMOTESOS + user_grp.EMOTEWOW + 
           user_grp.sicuro + user_grp.scusa + user_grp.dispiace + user_grp.disturbo + 
           user_grp.dimmi + user_grp.male + user_grp.lui + user_grp.lei + user_grp.loro + 
           user_grp.voi + user_grp.nervoso + user_grp.triste + user_grp.interessa + 
           user_grp.secondoMe + user_grp.secondoTe + user_grp.nonRiesco + 
           user_grp.riesco + user_grp.impazzi + user_grp.preoccupato + 
           user_grp.incubo + user_grp.aspettare + user_grp.pensare + 
           user_grp.scocciare + user_grp.stufo + user_grp.conto + user_grp.pazienza + 
           user_grp.consapevole + user_grp.chePalle + user_grp.importa + 
           user_grp.nonImporta + user_grp.frustrante + user_grp.merito + 
           user_grp.colpa + user_grp.disperato + user_grp.conseguenza + 
           user_grp.causa + user_grp.perdono + user_grp.sento + user_grp.senti + 
           user_grp.comeSenti + user_grp.si + user_grp.no + user_grp.niente + 
           user_grp.assolutamente + user_grp.tu + user_personal.domanda + 
           user_personal.esclamativo + user_personal.virgole_punti + 
           user_personal.EMOTEGOOD + user_personal.EMOTELOVE + user_personal.EMOTEBAD + 
           user_personal.EMOTEWINK + user_personal.EMOTESHOCK + user_personal.EMOTEAMAZE + 
           user_personal.EMOTEZZZ + user_personal.EMOTESIII + user_personal.EMOTEAHHH + 
           user_personal.EMOTEEHHH + user_personal.EMOTEOHOH + user_personal.EMOTEIHIH + 
           user_personal.EMOTEAHAH + user_personal.EMOTEEHEH + user_personal.EMOTEAZZ + 
           user_personal.EMOTEDAIII + user_personal.cazzo + user_personal.cazzata + 
           user_personal.merda + user_personal.EMOTEAAA + user_personal.EMOTEOOO + 
           user_personal.EMOTEEEE + user_personal.EMOTESOS + user_personal.EMOTEBASTA + 
           user_personal.EMOTEWOW + user_personal.bello + user_personal.sicuro + 
           user_personal.NonLoSo + user_personal.boh + user_personal.bho + 
           user_personal.aiuto + user_personal.agitat + user_personal.ansia + 
           user_personal.giusto + user_personal.scusa + user_personal.dispiace + 
           user_personal.ascolto + user_personal.capisco + user_personal.disturbo + 
           user_personal.dimmi + user_personal.bene + user_personal.male + 
           user_personal.ok + user_personal.mai + user_personal.sempre + 
           user_personal.impossibile + user_personal.io + user_personal.lui + 
           user_personal.lei + user_personal.loro + user_personal.voi + 
           user_personal.nervoso + user_personal.triste + user_personal.interessa + 
           user_personal.secondoMe + user_personal.secondoTe + user_personal.vicino + 
           user_personal.umore + user_personal.nonRiesco + user_personal.riesco + 
           user_personal.giuMorale + user_personal.impazzi + user_personal.angoscia + 
           user_personal.oppresso + user_personal.preoccupato + user_personal.sensibile + 
           user_personal.incubo + user_personal.aspettare + user_personal.pensare + 
           user_personal.infastidire + user_personal.scocciare + user_personal.esasperato + 
           user_personal.pezzi + user_personal.stufo + user_personal.accorgersi + 
           user_personal.conto + user_personal.pazienza + user_personal.consapevole + 
           user_personal.scrupoloso + user_personal.sensato + user_personal.responsabile + 
           user_personal.inconsciente + user_personal.chePalle + user_personal.importa + 
           user_personal.NonMImporta + user_personal.nonImporta + user_personal.frustrante + 
           user_personal.merito + user_personal.colpa + user_personal.disperato + 
           user_personal.sopportare + user_personal.conseguenza + user_personal.causa + 
           user_personal.perdono + user_personal.sento + user_personal.comeSento + 
           user_personal.senti + user_personal.comeSenti + user_personal.si + 
           user_personal.no + user_personal.niente + user_personal.assolutamente + 
           user_personal.tu + others_grp.domanda + others_grp.esclamativo + 
           others_grp.virgole_punti + others_grp.EMOTEGOOD + others_grp.EMOTELOVE + 
           others_grp.EMOTEBAD + others_grp.EMOTEWINK + others_grp.EMOTESHOCK + 
           others_grp.EMOTEAMAZE + others_grp.EMOTEZZZ + others_grp.EMOTESIII + 
           others_grp.EMOTENOOO + others_grp.EMOTEAHHH + others_grp.EMOTEEHHH + 
           others_grp.EMOTEOHOH + others_grp.EMOTEIHIH + others_grp.EMOTEAHAH + 
           others_grp.EMOTEEHEH + others_grp.EMOTEAZZ + others_grp.EMOTEDAIII + 
           others_grp.cazzo + others_grp.cazzata + others_grp.merda + 
           others_grp.EMOTEAAA + others_grp.EMOTEOOO + others_grp.EMOTEEEE + 
           others_grp.EMOTELOL + others_grp.EMOTESOS + others_grp.EMOTEBASTA + 
           others_grp.EMOTEWOW + others_grp.bello + others_grp.sicuro + 
           others_grp.NonLoSo + others_grp.boh + others_grp.agitat + 
           others_grp.giusto + others_grp.scusa + others_grp.disturbo + 
           others_grp.dimmi + others_grp.bene + others_grp.sempre + 
           others_grp.lei + others_grp.loro + others_grp.nervoso + others_grp.interessa + 
           others_grp.secondoMe + others_grp.vicino + others_grp.preoccupato + 
           others_grp.pensare + others_grp.esasperato + others_grp.stufo + 
           others_grp.conto + others_grp.responsabile + others_grp.inconsciente + 
           others_grp.importa + others_grp.disperato + others_grp.sopportare + 
           others_grp.perdono + others_grp.sento + others_grp.no + others_grp.niente + 
           others_personal.domanda + others_personal.EMOTEGOOD + others_personal.EMOTEBAD + 
           others_personal.EMOTEWINK + others_personal.EMOTEEHHH + others_personal.EMOTEEHEH + 
           others_personal.EMOTEAZZ + others_personal.cazzo + others_personal.cazzata + others_personal.EMOTEAAA + others_personal.EMOTEOOO + 
           others_personal.EMOTEEEE + others_personal.EMOTELOL + others_personal.EMOTESOS + 
           others_personal.EMOTEBASTA + others_personal.EMOTEWOW + others_personal.bello + 
           others_personal.sicuro + others_personal.NonLoSo + others_personal.boh + 
           others_personal.bho + others_personal.aiuto + others_personal.agitat + 
           others_personal.ansia + others_personal.giusto + others_personal.scusa + 
           others_personal.dispiace + others_personal.ascolto + others_personal.disturbo + 
           others_personal.dimmi + others_personal.bene + others_personal.male + 
           others_personal.ok + others_personal.mai + others_personal.sempre + 
           others_personal.impossibile + others_personal.io + others_personal.lui + 
           others_personal.lei + others_personal.loro + others_personal.voi + 
           others_personal.nervoso + others_personal.triste + others_personal.interessa + 
           others_personal.secondoMe + others_personal.secondoTe + others_personal.vicino + 
           others_personal.umore + others_personal.nonRiesco + others_personal.riesco + 
           others_personal.giuMorale + others_personal.impazzi + others_personal.angoscia + 
           others_personal.oppresso + others_personal.preoccupato + 
           others_personal.sensibile + others_personal.incubo + others_personal.aspettare + 
           others_personal.pensare + others_personal.infastidire + others_personal.scocciare + 
           others_personal.esasperato + others_personal.pezzi + others_personal.stufo + 
           others_personal.accorgersi + others_personal.conto + others_personal.pazienza + 
           others_personal.consapevole + others_personal.scrupoloso + 
           others_personal.sensato + others_personal.responsabile + 
           others_personal.inconsciente + others_personal.chePalle + 
           others_personal.importa + others_personal.NonMImporta + others_personal.nonImporta + 
           others_personal.frustrante + others_personal.merito + others_personal.colpa + 
           others_personal.disperato + others_personal.sopportare + 
           others_personal.conseguenza + others_personal.causa + others_personal.perdono + 
           others_personal.sento + others_personal.comeSento + others_personal.senti + 
           others_personal.si + others_personal.no + others_personal.niente + 
           others_personal.assolutamente + others_personal.tu + wall_azioni.w_amicizia + 
           wall_azioni.w_stato + wall_azioni.w_piace + wall_azioni.w_condiviso + 
           wall_azioni.w_linkAltri + wall_azioni.w_linkTuo + wall_azioni.w_partecipato + 
           wall_azioni.w_postInBacheca + wall_azioni.w_aggiornImgProf + 
           wall_azioni.w_nuovaFoto + wall_azioni.w_postTotali + wall_freq_ore.00 + 
           wall_freq_ore.01 + wall_freq_ore.03 + wall_n_days_active + H_openess + H_emotional + H_agreebleness + 
           I_emotional_regulation + z1 + z7 + z8 + M_neg + M_csc, 
         family = binomial, data = X.train)

step(fit5)

modellofinale=glm(y.train ~ msg_nchar_stats.nchar_per_text.Median + msg_MFprops.femmine + 
                    msg_freq_user.freqFriend1 + msg_freq_user.freqFriend2 + msg_freq_ore.03 + 
                    msg_freq_ore.04 + msg_freq_ore.07 + msg_freq_ore.15 + msg_freq_ore.16 + 
                    msg_freq_ore.17 + msg_freq_ore.18 + user_grp.esclamativo + 
                    user_grp.EMOTEGOOD + user_grp.EMOTEZZZ + user_grp.EMOTESIII + 
                    user_grp.EMOTENOOO + user_grp.EMOTEOHOH + user_grp.EMOTEAZZ + 
                    user_grp.EMOTEOOO + user_grp.EMOTESOS + user_grp.EMOTEWOW + 
                    user_grp.sicuro + user_grp.scusa + user_grp.dispiace + user_grp.disturbo + 
                    user_grp.dimmi + user_grp.male + user_grp.lui + user_grp.lei + 
                    user_grp.loro + user_grp.voi + user_grp.nervoso + user_grp.triste + 
                    user_grp.interessa + user_grp.secondoMe + user_grp.secondoTe + 
                    user_grp.nonRiesco + user_grp.riesco + user_grp.impazzi + 
                    user_grp.preoccupato + user_grp.incubo + user_grp.aspettare + 
                    user_grp.pensare + user_grp.scocciare + user_grp.stufo + 
                    user_grp.conto + user_grp.pazienza + user_grp.consapevole + 
                    user_grp.chePalle + user_grp.importa + user_grp.nonImporta + 
                    user_grp.frustrante + user_grp.merito + user_grp.colpa + 
                    user_grp.disperato + user_grp.conseguenza + user_grp.causa + 
                    user_grp.perdono + user_grp.sento + user_grp.senti + user_grp.comeSenti + 
                    user_grp.si + user_grp.no + user_grp.niente + user_grp.assolutamente + 
                    user_grp.tu + user_personal.domanda + user_personal.esclamativo + 
                    user_personal.virgole_punti + user_personal.EMOTEGOOD + user_personal.EMOTELOVE + 
                    user_personal.EMOTEBAD + user_personal.EMOTEWINK + user_personal.EMOTESHOCK + 
                    user_personal.EMOTEAMAZE + user_personal.EMOTEZZZ + user_personal.EMOTESIII + 
                    user_personal.EMOTEAHHH + user_personal.EMOTEEHHH + user_personal.EMOTEOHOH + 
                    user_personal.EMOTEIHIH + user_personal.EMOTEAHAH + user_personal.EMOTEEHEH + 
                    user_personal.EMOTEAZZ + user_personal.EMOTEDAIII + user_personal.cazzo + 
                    user_personal.cazzata + user_personal.merda + user_personal.EMOTEAAA + 
                    user_personal.EMOTEOOO + user_personal.EMOTEEEE + user_personal.EMOTESOS + 
                    user_personal.EMOTEBASTA + user_personal.EMOTEWOW + user_personal.bello + 
                    user_personal.sicuro + user_personal.NonLoSo + user_personal.boh + 
                    user_personal.bho + user_personal.aiuto + user_personal.agitat + 
                    user_personal.ansia + user_personal.giusto + user_personal.scusa + 
                    user_personal.dispiace + user_personal.ascolto + user_personal.capisco + 
                    user_personal.disturbo + user_personal.dimmi + user_personal.bene + 
                    user_personal.male + user_personal.ok + user_personal.mai + 
                    user_personal.sempre + user_personal.impossibile + user_personal.io + 
                    user_personal.lui + user_personal.lei + user_personal.loro + 
                    user_personal.voi + user_personal.nervoso + user_personal.triste + 
                    user_personal.interessa + user_personal.secondoMe + user_personal.secondoTe + 
                    user_personal.vicino + user_personal.umore + user_personal.nonRiesco + 
                    user_personal.riesco + user_personal.giuMorale + user_personal.impazzi + 
                    user_personal.angoscia + user_personal.oppresso + user_personal.preoccupato + 
                    user_personal.sensibile + user_personal.incubo + user_personal.aspettare + 
                    user_personal.pensare + user_personal.infastidire + user_personal.scocciare + 
                    user_personal.esasperato + user_personal.pezzi + user_personal.stufo + 
                    user_personal.accorgersi + user_personal.conto + user_personal.pazienza + 
                    user_personal.consapevole + user_personal.scrupoloso + user_personal.sensato + 
                    user_personal.responsabile + user_personal.inconsciente + 
                    user_personal.chePalle + user_personal.importa + user_personal.NonMImporta + 
                    user_personal.nonImporta + user_personal.frustrante + user_personal.merito + 
                    user_personal.colpa + user_personal.disperato + user_personal.sopportare + 
                    user_personal.conseguenza + user_personal.causa + user_personal.perdono + 
                    user_personal.sento + user_personal.comeSento + user_personal.senti + 
                    user_personal.comeSenti + user_personal.si + user_personal.no + 
                    user_personal.niente + user_personal.assolutamente + user_personal.tu + 
                    others_grp.domanda + others_grp.esclamativo + others_grp.virgole_punti + 
                    others_grp.EMOTEGOOD + others_grp.EMOTELOVE + others_grp.EMOTEBAD + 
                    others_grp.EMOTEWINK + others_grp.EMOTESHOCK + others_grp.EMOTEAMAZE + 
                    others_grp.EMOTEZZZ + others_grp.EMOTESIII + others_grp.EMOTENOOO + 
                    others_grp.EMOTEAHHH + others_grp.EMOTEEHHH + others_grp.EMOTEOHOH + 
                    others_grp.EMOTEIHIH + others_grp.EMOTEAHAH + others_grp.EMOTEEHEH + 
                    others_grp.EMOTEAZZ + others_grp.EMOTEDAIII + others_grp.cazzo + 
                    others_grp.cazzata + others_grp.merda + others_grp.EMOTEAAA + 
                    others_grp.EMOTEOOO + others_grp.EMOTEEEE + others_grp.EMOTELOL + 
                    others_grp.EMOTESOS + others_grp.EMOTEBASTA + others_grp.EMOTEWOW + 
                    others_grp.bello + others_grp.sicuro + others_grp.NonLoSo + 
                    others_grp.boh + others_grp.agitat + others_grp.giusto + 
                    others_grp.scusa + others_grp.disturbo + others_grp.dimmi + 
                    others_grp.bene + others_grp.sempre + others_grp.lei + others_grp.loro + 
                    others_grp.nervoso + others_grp.interessa + others_grp.secondoMe + 
                    others_grp.vicino + others_grp.preoccupato + others_grp.pensare + 
                    others_grp.esasperato + others_grp.stufo + others_grp.conto + 
                    others_grp.responsabile + others_grp.inconsciente + others_grp.importa + 
                    others_grp.disperato + others_grp.sopportare + others_grp.perdono + 
                    others_grp.sento + others_grp.no + others_grp.niente + others_personal.domanda + 
                    others_personal.EMOTEGOOD + others_personal.EMOTEBAD + others_personal.EMOTEWINK + 
                    others_personal.EMOTEEHHH + others_personal.EMOTEEHEH + others_personal.EMOTEAZZ + 
                    others_personal.cazzo + others_personal.cazzata + others_personal.EMOTEAAA + 
                    others_personal.EMOTEOOO + others_personal.EMOTEEEE + others_personal.EMOTELOL + 
                    others_personal.EMOTESOS + others_personal.EMOTEBASTA + others_personal.EMOTEWOW + 
                    others_personal.bello + others_personal.sicuro + others_personal.NonLoSo + 
                    others_personal.boh + others_personal.bho + others_personal.aiuto + 
                    others_personal.agitat + others_personal.ansia + others_personal.giusto + 
                    others_personal.scusa + others_personal.dispiace + others_personal.ascolto + 
                    others_personal.disturbo + others_personal.dimmi + others_personal.bene + 
                    others_personal.male + others_personal.ok + others_personal.mai + 
                    others_personal.sempre + others_personal.impossibile + others_personal.io + 
                    others_personal.lui + others_personal.lei + others_personal.loro + 
                    others_personal.voi + others_personal.nervoso + others_personal.triste + 
                    others_personal.interessa + others_personal.secondoMe + others_personal.secondoTe + 
                    others_personal.vicino + others_personal.umore + others_personal.nonRiesco + 
                    others_personal.riesco + others_personal.giuMorale + others_personal.impazzi + 
                    others_personal.angoscia + others_personal.oppresso + others_personal.preoccupato + 
                    others_personal.sensibile + others_personal.incubo + others_personal.aspettare + 
                    others_personal.pensare + others_personal.infastidire + others_personal.scocciare + 
                    others_personal.esasperato + others_personal.pezzi + others_personal.stufo + 
                    others_personal.accorgersi + others_personal.conto + others_personal.pazienza + 
                    others_personal.consapevole + others_personal.scrupoloso + 
                    others_personal.sensato + others_personal.responsabile + 
                    others_personal.inconsciente + others_personal.chePalle + 
                    others_personal.importa + others_personal.NonMImporta + others_personal.nonImporta + 
                    others_personal.frustrante + others_personal.merito + others_personal.colpa + 
                    others_personal.disperato + others_personal.sopportare + 
                    others_personal.conseguenza + others_personal.causa + others_personal.perdono + 
                    others_personal.sento + others_personal.comeSento + others_personal.senti + 
                    others_personal.si + others_personal.no + others_personal.niente + 
                    others_personal.assolutamente + others_personal.tu + wall_azioni.w_amicizia + 
                    wall_azioni.w_stato + wall_azioni.w_piace + wall_azioni.w_condiviso + 
                    wall_azioni.w_linkAltri + wall_azioni.w_linkTuo + wall_azioni.w_partecipato + 
                    wall_azioni.w_postInBacheca + wall_azioni.w_aggiornImgProf + 
                    wall_azioni.w_nuovaFoto + wall_azioni.w_postTotali + wall_freq_ore.00 + 
                    wall_freq_ore.01 + wall_freq_ore.03 + wall_n_days_active + 
                    H_openess + H_emotional + H_agreebleness + I_emotional_regulation + 
                    z1 + z7,family=binomial,data=X.train,na.action = "na.exclude")

step(modellofinale)

########################

dim(X.test)

yhat=rep(NA,70)
for(i in 1:70){
  yhat[i]=predict(modellofinale,newdata=data.frame(X.test[i,]),type="response")
}
yhat
table(y.test,yhat>0.5)
(26+6)/70

library(pROC)
plot(roc(y.test,yhat),legacy.axes=T,print.auc=T,asp=F)
