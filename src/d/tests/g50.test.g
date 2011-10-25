{
#define start
#define reject
#define import
#define def
#define pop
#define id
}

Program: [start] Module? DeclDef*;

//Module
Module: 'module' ('(''system'')')? IdentifierList ';';
Import: 'import' (IdentifierList {import}) ( ',' (IdentifierList {import}) )* ';';
ConditionalDeclaration: Condition ':' | Condition DeclarationBlock ('else' DeclarationBlock)?;
Condition: VersionCondition | DebugCondition | StaticIfCondition;
VersionSpecification: 'version' '=' (Integer|Identifier) ';';
AttributeSpecifier: Attribute* ( DeclarationBlock | ':' DeclDef* );
VersionCondition: 'version' '(' (Integer|Identifier) ')';
DebugCondition: 'debug' ('(' (Integer|Identifier) ')')?;
StaticIfCondition: 'static' 'if' '(' Expression ')';

//Attribute
Attribute: StorageClassAttribute | ProtectionAttribute | LinkageAttribute | AlignAttribute;
StorageClassAttribute: 'synchronized'|'static'|'final'|'override'|'abstract'|'const'|'auto'|'scope'|'pure';
ProtectionAttribute: 'private'|'package'|'protected'|'public'|'export';
LinkageAttribute: 'extern' ('(' ('C'|'C++'|'D'|'System'|'Windows') ')')?;
AlignAttribute: 'align' ( '(' Integer ')' )?;

//Type
Type : ("bool|byte|ubyte|short|ushort|int|uint|long|ulong|char|wchar|dchar|float|double|real|void"
         | TemplateIdentifierList | ('const'|'invariant') '(' Type ')')
       ( ('['(Expression)?']') | '*')* (('delegate'|'function') '(' Parameter? (',' Parameter )* ')' )?;
TypeSpecialization: Type | "typedef|struct|union|class|interface|enum|function|delegate|super|return";
TemplateInstance: Identifier ('!' '(' TemplateArgumentList ')')?;
TemplateParameter: TemplateAliasParameter | TemplateTupleParameter | TemplateValueParameter | TemplateTypeParameter;
TemplateAliasParameter: 'alias' Identifier (':' Type)? ('=' Type)?;
TemplateTupleParameter: Identifier '...';
TemplateValueParameter: Type Declarator (':' Expression)? ('=' Expression)?;
TemplateTypeParameter: Identifier (':' Type)? ('=' Type)?;
TemplateArgument: Type | Expression | Identifier;

//Initializer
Initializer: 'void' | NonVoidInitializer;
NonVoidInitializer: Expression | '[' MemberInitializerList ']' | '{' MemberInitializerList '}';
MemberInitializer: Identifier ':' NonVoidInitializer;

//Declaration
DeclarationBlock: DeclDef | '{' DeclDef* '}';
DeclDef
 : Import | Function | Declaration ';' | Struct | Class | SpecialMethod
 | VersionSpecification | ConditionalDeclaration | AttributeSpecifier
 | 'static' ('this'|'~this') '(' ')' BlockStatement
 | 'static' 'assert' '(' Expression (',' Expression )? ')'
 | 'unittest' BlockStatement
 | 'enum' Identifier? (':' Type)? (';' | '{' EnumMemberList '}' )
 | 'enum' Type Declarator '=' Initializer ';'
 | 'mixin' '(' Expression ')' ';'
 | 'union' Identifier? '{' DeclDef* '}'
;
EnumMember: Identifier ('=' Expression )?;
Declaration: ('typedef'|'alias')? ('auto'|Type) Declarator ('=' Initializer)? (',' Identifier ('=' Initializer)? )*;
Declarator: Identifier {def} ('['(Expression|Type)?']')* {pop};

//Structure
Struct: 'static'? 'struct' Identifier {def} ('(' TemplateParameterList ')')? '{' DeclDef* '}' {pop};
Interface: 'interface' Identifier {def} ('(' TemplateParameterList ')')? ( ':' BaseClassList )? '{' DeclDef* '}' {pop};
Class: 'static'? 'class' Identifier {def} ('(' TemplateParameterList ')')? ( ':' BaseClassList )? '{' DeclDef* '}' {pop};
BaseClass: ('private'|'package'|'public'|'export')? TemplateIdentifierList;
SpecialMethod: (('this'|'~this') {def}) '(' ParameterList? ')' BlockStatement {pop};

//Function
Function: Type Identifier {def} ('(' TemplateParameterList ')')? '(' ( | '...' | ParameterList (',' '...')? ) ')' (';' | BlockStatement) {pop};
Parameter: InOut? ParameterStorageClass* Type Declarator? ('=' Initializer)?;
InOut: 'inout'|'in'|'out'|'ref'|'lazy';
ParameterStorageClass: 'const'|'invariant'|'final'|'scope'|'static';
BlockStatement: '{' Statement* '}';

Statement
 : DeclDef
 | BlockStatement
 | Condition Statement ('else' Statement)?
 | Expression ';'
 | Identifier ':' Statement
 | 'if' '(' Expression ')' Statement ('else' Statement)?
 | 'while' '(' Expression ')' Statement
 | 'do' Statement 'while' Expression
 | 'for' '(' (Declaration|Expression)? ';' Expression? ';' Expression? ')' Statement
 | ('foreach'|'foreach_reverse') '(' (Type Declarator|Identifier) (',' (Type Declarator|Identifier) )? ';' Expression ')' Statement
 | 'return' Expression ';'
 | 'with' '(' Expression ')' Statement
 | 'asm' '{' AsmInstruction* '}'
 | 'throw' Expression ';'
 | 'scope' '(' ('exit'|'failure'|'success') ')' Statement
 ;

Expression
 : Literal
 | Identifier //{id}
 | ('-' | '+' | '~' | '!' | '*' | '&' | '--' | '++') Expression
 | Expression ('--'|'++')
 | Expression '(' ArgumentList ')' //{call}
 | Expression '[' ( ArgumentList | Expression '..' Expression ) ']' //{index}
 | Expression '.' Expression                                                            $binary_op_left 9 //{dot}
 | Expression ('*'|'/'|'%') Expression		                                            $binary_op_left 8
 | Expression ('+'|'~'|'-')	Expression	                                                $binary_op_left 7
 | Expression ('<<'|'>>') Expression		                                            $binary_op_left 6
 | Expression ('<'|'<='|'>='|'>') Expression		                                    $binary_op_left 5
 | Expression ('=='|'!='|'is'|'in') Expression                                          $binary_op_left 4
 | Expression ('&'|'^'|'|') Expression  	                                        	$binary_op_left 3
 | Expression ('&&'|'||') Expression		                                            $binary_op_left 2
 | Expression ('='|'*='|'/='|'%=''+='|'~='|'-='|'<<='|'>>='|'&='|'|='|'^=') Expression	$binary_op_left 1
 | Expression '?' Expression ':' Expression
 | (('function'|'delegate'|) {def}) ('(' ParameterList? ')')? '{' Statement* '}' {pop}
 | '(' Expression ')'
 | ('is'|'!is') '(' Type Identifier? ( (':'|'==') TypeSpecialization )? (',' TemplateParameterList)? ')'
 | '[' ArgumentList ']'
 | '[' KeyValueList ']'
 | 'cast' '(' ('invariant'|'const')? Type ')' Expression
 | 'new' Type ( '[' ArgumentList ']' | '(' ArgumentList ')' )
;
KeyValue: Expression ':' Expression;

Identifier: "[a-zA-Z_][_a-zA-Z0-9]*" [reject];
Literal: Character | String+ | Integer | Float | '$' | 'this' | 'super' | 'null' | 'true' | 'false';
Character: "'([^'\\]|\\['\\abfnrtv0x])*'";
String: "\"([^\"\\]|\\[\"\\abfnrtv0x])*\"" | 'q{' Tokens* '}';
Integer: "-?(0b[0-1]*|[0-9_]*|0[xX][0-9a-fA-F]*)[uUbBwWLl]*";
Float: "[\-+]?([0-9_]+\.[0-9_]*|\.[0-9_]+)([eE][\-+]?[0-9]+)?";
Tokens: "[^{}]*" | '{' Tokens* '}';
AsmInstruction: "[^{}]*";

//List
IdentifierList: '.'? Identifier ('.' Identifier)*;
TemplateIdentifierList: (Identifier|TemplateInstance) ('.' (Identifier|TemplateInstance))*;
BaseClassList: BaseClass (',' BaseClass )*;
EnumMemberList: (EnumMember (',' EnumMember )* )?;
MemberInitializerList: (MemberInitializer (',' MemberInitializer )* )?;
ParameterList: Parameter (',' Parameter)*;
ArgumentList: (Expression (',' Expression)* )?;
KeyValueList: KeyValue (',' KeyValue)*;
TemplateArgumentList: (TemplateArgument (',' TemplateArgument)* )?;
TemplateParameterList: (TemplateParameter (',' TemplateParameter)* )?;

whitespace: ( "[ \t\r\n]+" | singleLineComment | multiLineComment | nestedComment )*;
singleLineComment: '//' "[^\n]*" '\n';
multiLineComment: '/*' ( "[^*]" | '*'+ "[^*\/]" )* '*'+ '/';
nestedComment: '/+' ( nestedComment | ( "[^+]" | '+'+ "[^+\/]" )* '+'+ )* ( "[^+]" | '+'+ "[^+\/]" )* '+'+ '/';
