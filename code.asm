.data
shrek: .asciiz "Get shrekt.\n"

.text
main:
    li $v0, 4
    la $a0, shrek
    syscall
