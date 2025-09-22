// js/components/views/audiogram/chart-symbols.js
// Función drawSymbol con todos los símbolos audiológicos estándar

Object.assign(AudiogramChartView.prototype, {

  drawSymbol(x, y, symbol, color) {
    const ctx = this.ctx;
    const size = this.symbolSize;
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 2;

    switch (symbol) {
      case 'circle': // O - Aérea OD sin masking
        ctx.beginPath();
        ctx.arc(x, y, size, 0, 2 * Math.PI);
        ctx.stroke();
        break;

      case 'x': // X - Aérea OI sin masking
        ctx.beginPath();
        ctx.moveTo(x - size, y - size);
        ctx.lineTo(x + size, y + size);
        ctx.moveTo(x + size, y - size);
        ctx.lineTo(x - size, y + size);
        ctx.stroke();
        break;

      case 'square': // □ - Aérea OI con masking
        ctx.beginPath();
        ctx.rect(x - size, y - size, size * 2, size * 2);
        ctx.stroke();
        break;

      case 'triangle': // △ - Aérea OD con masking
        ctx.beginPath();
        ctx.moveTo(x, y - size);
        ctx.lineTo(x - size, y + size);
        ctx.lineTo(x + size, y + size);
        ctx.closePath();
        ctx.stroke();
        break;

      case 'bone_left': // < - Ósea OD sin masking
        ctx.beginPath();
        ctx.moveTo(x - this.boneOffset + size, y - size);
        ctx.lineTo(x - this.boneOffset - size, y);
        ctx.moveTo(x - this.boneOffset - size, y);
        ctx.lineTo(x - this.boneOffset + size, y + size);
        ctx.stroke();
        break;

      case 'bone_right': // > - Ósea OI sin masking
        ctx.beginPath();
        ctx.moveTo(x + this.boneOffset - size, y - size);
        ctx.lineTo(x + this.boneOffset + size, y);
        ctx.moveTo(x + this.boneOffset + size, y);
        ctx.lineTo(x + this.boneOffset - size, y + size);
        ctx.stroke();
        break;

      case 'bone_bracket_left': // [ - Ósea OD con masking
        const leftX = x - this.boneOffset;
        ctx.beginPath();
        ctx.moveTo(leftX - size, y - size);
        ctx.lineTo(leftX - size/2, y - size);
        ctx.moveTo(leftX - size, y - size);
        ctx.lineTo(leftX - size, y + size);
        ctx.moveTo(leftX - size, y + size);
        ctx.lineTo(leftX - size/2, y + size);
        ctx.stroke();
        break;

      case 'bone_bracket_right': // ] - Ósea OI con masking
        const rightX = x + this.boneOffset;
        ctx.beginPath();
        ctx.moveTo(rightX + size, y - size);
        ctx.lineTo(rightX + size/2, y - size);
        ctx.moveTo(rightX + size, y - size);
        ctx.lineTo(rightX + size, y + size);
        ctx.moveTo(rightX + size, y + size);
        ctx.lineTo(rightX + size/2, y + size);
        ctx.stroke();
        break;

      case 'ldl_present': // Triángulo rectángulo - LDL presente
        const ldlX = (color === this.config.colors.od) ? x - this.ldlOffsetX : x + this.ldlOffsetX;
        const ldlY = y - this.ldlOffsetY;
        ctx.beginPath();
        if (color === this.config.colors.od) {
          ctx.moveTo(ldlX - size, ldlY + size);
          ctx.lineTo(ldlX + size, ldlY + size);
          ctx.lineTo(ldlX + size, ldlY - size);
        } else {
          ctx.moveTo(ldlX + size, ldlY + size);
          ctx.lineTo(ldlX - size, ldlY + size);
          ctx.lineTo(ldlX - size, ldlY - size);
        }
        ctx.closePath();
        ctx.stroke();
        break;

      case 'ldl_absent': // Triángulo rectángulo + flecha - LDL ausente
        const absentX = (color === this.config.colors.od) ? x - this.ldlOffsetX : x + this.ldlOffsetX;
        const absentY = y - this.ldlOffsetY;
        
        // Triángulo rectángulo
        ctx.beginPath();
        if (color === this.config.colors.od) {
          ctx.moveTo(absentX - size, absentY + size);
          ctx.lineTo(absentX + size, absentY + size);
          ctx.lineTo(absentX + size, absentY - size);
        } else {
          ctx.moveTo(absentX + size, absentY + size);
          ctx.lineTo(absentX - size, absentY + size);
          ctx.lineTo(absentX - size, absentY - size);
        }
        ctx.closePath();
        ctx.stroke();
        
        // Línea vertical + flecha
        const lineStartX = (color === this.config.colors.od) ? absentX + size : absentX - size;
        const lineEndY = absentY + size * 2;
        ctx.beginPath();
        ctx.moveTo(lineStartX, absentY + size);
        ctx.lineTo(lineStartX, lineEndY);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(lineStartX - size/2, lineEndY - size/2);
        ctx.lineTo(lineStartX, lineEndY);
        ctx.lineTo(lineStartX + size/2, lineEndY - size/2);
        ctx.stroke();
        break;

      case 'arrow': // Flecha hacia abajo - No response
        ctx.beginPath();
        ctx.moveTo(x, y - size * 1.5);
        ctx.lineTo(x, y + size * 1.5);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x - size, y + size);
        ctx.lineTo(x, y + size * 1.5);
        ctx.lineTo(x + size, y + size);
        ctx.stroke();
        break;

      case 'no_response_circle': // O + flecha ↓
        ctx.beginPath();
        ctx.arc(x, y, size, 0, 2 * Math.PI);
        ctx.stroke();
        // Flecha hacia abajo
        ctx.beginPath();
        ctx.moveTo(x, y + size + 2);
        ctx.lineTo(x, y + size + 8);
        ctx.moveTo(x - 3, y + size + 5);
        ctx.lineTo(x, y + size + 8);
        ctx.lineTo(x + 3, y + size + 5);
        ctx.stroke();
        break;

      case 'no_response_x': // X + flecha ↓
        ctx.beginPath();
        ctx.moveTo(x - size, y - size);
        ctx.lineTo(x + size, y + size);
        ctx.moveTo(x + size, y - size);
        ctx.lineTo(x - size, y + size);
        ctx.stroke();
        // Flecha hacia abajo
        ctx.beginPath();
        ctx.moveTo(x, y + size + 2);
        ctx.lineTo(x, y + size + 8);
        ctx.moveTo(x - 3, y + size + 5);
        ctx.lineTo(x, y + size + 8);
        ctx.lineTo(x + 3, y + size + 5);
        ctx.stroke();
        break;

      case 'vt_circle': // O + "VT"
        ctx.beginPath();
        ctx.arc(x, y, size, 0, 2 * Math.PI);
        ctx.stroke();
        ctx.font = '8px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('VT', x, y + 15);
        break;

      case 'vt_x': // X + "VT"
        ctx.beginPath();
        ctx.moveTo(x - size, y - size);
        ctx.lineTo(x + size, y + size);
        ctx.moveTo(x + size, y - size);
        ctx.lineTo(x - size, y + size);
        ctx.stroke();
        ctx.font = '8px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('VT', x, y + 15);
        break;
    }
  }

});