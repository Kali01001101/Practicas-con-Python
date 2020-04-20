#Este es un resumen de mis practicas realizadas con Python.

####################		
#LISTAS
####################

valor1=0
cuit=[]
num=[5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

for k in range(11): 
    inuser= int(input("Ingrese su CUIT/CUIL: "))
    cuit.append(inuser)
for x in range(10):
    aux1 = cuit[x]*num[x]
    valor1 = aux1+valor1
valor2= valor1%11
valor3= 11-valor2
if valor3==11:
    digitoV=0
if valor3==10:
    digitoV=9
else:
    digitoV=valor3
if digitoV==cuit[10]:
	print("Muchas gracias")
else:
	print("Revise el CUIT/CUIL ingresado")

####################


lista=[]
for x in range(5):
    num= int(input("Ingrese un numero: "))
    lista.append(num)
print ("Lista sin ordenar", lista)
for k in range(4):
    for x in range(4-k):
        if lista[x]>lista[x+1]:
            var=lista[x]
            lista[x]=lista[x+1]
            lista[x+1]=var
print ("Lista ordenada de menor a mayor: ", lista)

for k in range(4):
    for x in range(4-k):
        if lista[x]<lista[x+1]:
            var=lista[x]
            lista[x]=lista[x+1]
            lista[x+1]=var
print ("Lista ordenada de mayor a menor ",lista)

####################

paises= []
for x in range(5):
	nombre= input("Ingrese el pais: ")
	paises.append(nombre)
print ("lista sin ordenar: ", paises)
for k in range(4):
	for x in range(4-k):
			if paises[x]>paises[x+1]:
				var= paises[x]
				paises[x]=paises[x+1]
				paises[x+1]=var
print ("lista ordenada: ", paises)

####################

lista1=[]
lista2=[]
suma=[]
for x in range(4):
	num1= int(input("Ingrese un numero para la primer lista: "))
	lista1.append(num1)
	num2= int(input("Ingrese un numero para la segunda lista: "))
	lista2.append(num2)
	sumas= lista1[x] + lista2[x]
	suma.append(sumas)
print (suma)

####################

lista= ["Maximo", "Rodri", "carlos", "Mariano"]
cant=0
x=0
while x<len(lista[x]):
	if len(lista[x])>5:
		cant=cant+1
	x=x+1
print ("La cantidad de nombres con mas de 5 caracteres es: ", cant)

####################

altura= []
suma= 0
mayoraltura= 0
menoraltura= 0
for x in range(5):
	altvar= float(input("Ingrese la altura: "))
	altura.append(altvar)
	suma= suma+altvar
promedio= suma/5
for x in range(5):
	if altura[x]>promedio:
		mayoraltura= mayoraltura+1
	else:
		if altura[x]<promedio:
			menoraltura= menoraltura+1
	x=x+1	
print ("El promedio de altura de las 5 personas es: ", promedio)
print ("La cantidad de personas mas altas que el promedio es: ", mayoraltura)
print ("La cantidad de personas mas bajas que el promedio es: ", menoraltura)

####################

listatm=[]
listatt=[]

for x in range(4):
	sueldostm= float(input("Ingrese el sueldo de un empleado tm: "))
	listatm.append(sueldostm)
for x in range(4):
	sueldostt= float(input("Ingrese el sueldo de un empleado tt: "))
	listatt.append(sueldostt)
print ("Los sueldos de los empleados turno mañana son: ", listatm)
print ("Los sueldos de los empleados turno tarde son: ", listatt)

####################

lista= []
cant=0
for x in range(5):
	enteros= int(input("Ingrese un numero para agregar a la lista: "))
	lista.append(enteros)
mayor=lista[0]
for x in range(1,5):
	if lista[x]>mayor:
		mayor= lista[x]
for x in range(5):
	if mayor==lista[x]:
		cant=cant+1
if cant>1:
	print ("La cantidad de veces que se repite el numero es: ", cant)
		
print ("El numero de mayor valor en la lista es: ", mayor)

####################

productos=[]
precios=[]
cant=0
for x in range(5):
	varproduct= input("Ingrese el producto: ")
	productos.append(varproduct)
	varprecios= int(input("Ingrese el precio del producto: "))
	precios.append(varprecios)
mayor= precios[0]
for x in range(1,5):
	if precios[x]>mayor: 
		cant=cant+1
print ("La cantidad de productos de mayor precio al primero son: ", cant)

####################

nombre=[]
nota=[]
muybueno=[]
bueno=[]
insuficiente=[]
cant=0
for x in range(4):
	varnombre= input("Ingrese el nombre del alumno: ")
	nombre.append(varnombre)
	varnota= int(input("Ingrese la nota de este alumno: "))
	nota.append(varnota)
	if nota[x]>=8:
		muybueno.append(nombre[x])
		cant=cant+1
	if nota[x]>=4 and nota[x]<=7:
   		bueno.append(nombre[x])
	if nota[x]<4:
		insuficiente.append(nombre[x])
print ("Los alumnos que estan en condicion de muybueno son: ", muybueno)
print ("Los alumnos que estan en condicion de bueno son: ", bueno)
print ("Los alumnos que estan en condicion de insuficiente son: ", insuficiente)

####################
#FOR
####################

equilateros= 0
isosceles= 0 
escaleno= 0
n= int(input("Cuantos triangulos ingresara?:"))
for x in range(n):
	lado1= int(input("Ingrese el primer lado:"))
	lado2= int(input("Ingrese el segundo lado:"))
    lado3= int(input("Ingrese el tercer lado:"))
    if lado1==lado2 and lado2==lado3:
		equilateros= equilateros+1
	if lado1==lado2 or lado1==lado3 or lado2==lado3:
		isosceles= isosceles+1
	if lado1 != lado2 and lado2 != lado3 and lado3 != lado1:
		escaleno= escaleno+1

print ("La cantidad de triangulos equilateros es:", equilateros)
print ("La cantidad de triangulos isosceles es:", isosceles)
print ("La cantidad de triangulos escalenos es:", escaleno)


numero= int(input("Ingrese cuantos numeros cargara:"))
pares= 0
impares= 0 
for x in range(numero):
	valor=int(input("Ingrese el numero:"))
	if valor%2==0:
		pares= pares+1
	else:
		impares= impares+1


####################
#WHILE
####################

while x<=15:
	lista1=int(input("Ingrese el valor de la primera lista:"))
	
	primerlista= lista1+primerlista
	x=x+1
while y<=15:
	lista2=int(input("Ingrese el valor de la segunda lista:"))
	segundalista= lista2+segundalista
	y=y+1
if primerlista>segundalista:
	print("La primera lista es mayor")
elif primerlista<segundalista:
	print ("La segunda lista es mayor")
else:
	print ("Ambas listas tienen el mismo valor")

####################

x= 1
normales=0
altos =0
total=0
while x<=6:
	sueldo= int(input("Ingrese el sueldo del empleado:"))
	x=x+1
	total= total + sueldo
	if sueldo>=100 and sueldo<=300:
		normales= normales+1
	else:
		altos=altos+1
print ("Los empleados con un sueldo entre 100 y 300 son:")
print (normales)
print ("Los empleados con un sueldo mayor a 300 son:")
print (altos)
print ("El importe que gasta la empresa en sueldos al personal es de:")
print (total)

####################

x=1
notas7=0
notas0=0
while x<=10:
	notasm= int(input('Ingrese la nota del alumno:'))
	x= x+1
	if notasm>=7:
		notas7= notas7+1
	else:
		notas0=notas0+1
print ('La cantidad de alumnos que sacaron 7 o mas son:')
print (notas7)
print ('La cantidad de alumnos que sacaron menos de 7 son:')
print (notas0)
